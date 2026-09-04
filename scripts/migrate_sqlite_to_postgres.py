#!/usr/bin/env python3
"""
IPODecoded - SQLite to PostgreSQL / Neon Migration Utility
===========================================================
Migrates live data from local SQLite (ipodecoded.db) to PostgreSQL (e.g. Neon, Supabase).
- Read-only on SQLite: never alters, resets, or deletes the source SQLite database.
- Idempotent: can be safely re-run without duplicate key violations.
- Preserves exact primary keys, foreign keys, timestamps, and multi-source provenance.
- Synchronizes PostgreSQL SERIAL sequences (ipos_id_seq, ipo_gmp_id_seq, etc.).

Usage:
    # 1. Via command-line argument:
    python scripts/migrate_sqlite_to_postgres.py "postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"

    # 2. Or via TARGET_DATABASE_URL / DATABASE_URL environment variable:
    export TARGET_DATABASE_URL="postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"
    python scripts/migrate_sqlite_to_postgres.py
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.db import Base, IPO, IPOGMP, IPOSource, SourceHealth, PipelineRun


def get_target_url() -> str:
    # 1. From CLI argument
    if len(sys.argv) > 1 and sys.argv[1].strip():
        url = sys.argv[1].strip()
    else:
        # 2. From environment
        url = os.getenv("TARGET_DATABASE_URL", "").strip() or os.getenv("DATABASE_URL", "").strip()

    if not url:
        print("\n❌ Error: Target PostgreSQL URL is required.")
        print("Provide it as a command line argument or set TARGET_DATABASE_URL / DATABASE_URL.")
        print('Example: python scripts/migrate_sqlite_to_postgres.py "postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"\n')
        sys.exit(1)

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    if not url.startswith("postgresql"):
        print(f"\n❌ Error: Target URL must be a PostgreSQL connection string, got: {url[:25]}...\n")
        sys.exit(1)

    return url


def migrate():
    target_url = get_target_url()
    sqlite_path = BASE_DIR / "ipodecoded.db"

    if not sqlite_path.exists():
        print(f"❌ Error: Source SQLite file '{sqlite_path}' does not exist.")
        sys.exit(1)

    sqlite_url = f"sqlite:///{sqlite_path}"
    print("====================================================================")
    print("🚀 IPODecoded: SQLite → PostgreSQL / Neon Migration Utility")
    print("====================================================================")
    print(f"📁 Source: SQLite ({sqlite_path}) [READ-ONLY]")
    # Obfuscate password in printed target URL
    safe_target = target_url
    try:
        from urllib.parse import urlsplit, urlunsplit
        parsed = urlsplit(target_url)
        if parsed.password:
            safe_netloc = f"{parsed.username or ''}:****@{parsed.hostname or ''}"
            if parsed.port:
                safe_netloc += f":{parsed.port}"
            safe_target = urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment))
    except Exception:
        safe_target = "postgresql://****:****@target-db"
    print(f"🌐 Target: PostgreSQL ({safe_target})")
    print("--------------------------------------------------------------------")

    # 1. Connect to Source (SQLite) - strictly read-only
    src_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    SrcSession = sessionmaker(bind=src_engine)
    src_db = SrcSession()

    # 2. Connect to Target (PostgreSQL)
    tgt_engine = create_engine(target_url, pool_pre_ping=True, pool_recycle=300)
    TgtSession = sessionmaker(bind=tgt_engine)
    tgt_db = TgtSession()

    try:
        # Test connection
        with tgt_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Successfully connected to target PostgreSQL database.")

        # Create schema tables if not present
        print("📦 Creating target schema tables and indexes...")
        Base.metadata.create_all(bind=tgt_engine)

        # Defensive schema compatibility in case tables were pre-created via custom SQL DDL
        with tgt_engine.connect() as conn:
            conn.execute(text("ALTER TABLE ipo_sources ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ DEFAULT NOW();"))
            try:
                conn.execute(text("ALTER TABLE ipo_sources ALTER COLUMN raw_data TYPE TEXT USING raw_data::text;"))
            except Exception:
                pass
            conn.commit()

        print("✅ Schema tables ready.")
        print("--------------------------------------------------------------------")

        # 3. Migrate IPOs
        src_ipos = src_db.query(IPO).order_by(IPO.id).all()
        print(f"🔄 Migrating {len(src_ipos)} IPO master records...")
        ipo_inserted = 0
        ipo_skipped = 0

        for s_ipo in src_ipos:
            existing = tgt_db.query(IPO).filter((IPO.id == s_ipo.id) | (IPO.slug == s_ipo.slug)).first()
            if existing:
                ipo_skipped += 1
                continue

            new_ipo = IPO(
                id=s_ipo.id,
                company_name=s_ipo.company_name,
                slug=s_ipo.slug,
                ipo_type=s_ipo.ipo_type,
                status=s_ipo.status,
                open_date=s_ipo.open_date,
                close_date=s_ipo.close_date,
                allotment_date=s_ipo.allotment_date,
                refund_date=s_ipo.refund_date,
                demat_date=s_ipo.demat_date,
                listing_date=s_ipo.listing_date,
                price_band_low=s_ipo.price_band_low,
                price_band_high=s_ipo.price_band_high,
                lot_size=s_ipo.lot_size,
                minimum_investment=s_ipo.minimum_investment,
                issue_size=s_ipo.issue_size,
                fresh_issue=s_ipo.fresh_issue,
                ofs=s_ipo.ofs,
                face_value=s_ipo.face_value,
                subscription_status=s_ipo.subscription_status,
                subscription_retail=s_ipo.subscription_retail,
                subscription_qib=s_ipo.subscription_qib,
                subscription_nii=s_ipo.subscription_nii,
                subscription_total=s_ipo.subscription_total,
                company_description=s_ipo.company_description,
                source_name=s_ipo.source_name,
                source_url=s_ipo.source_url,
                source_id=s_ipo.source_id,
                master_data_validated=s_ipo.master_data_validated,
                gmp_sources_available=s_ipo.gmp_sources_available,
                gmp_divergence_alert=s_ipo.gmp_divergence_alert,
                is_cross_validated=s_ipo.is_cross_validated,
                has_conflicts=s_ipo.has_conflicts,
                conflicts_json=s_ipo.conflicts_json,
                sources_verified=s_ipo.sources_verified,
                gmp_investorgain=s_ipo.gmp_investorgain,
                gmp_ipowatch=s_ipo.gmp_ipowatch,
                current_gmp_secondary=s_ipo.current_gmp_secondary,
                gmp_spread=s_ipo.gmp_spread,
                gmp_spread_low=s_ipo.gmp_spread_low,
                gmp_spread_high=s_ipo.gmp_spread_high,
                created_at=s_ipo.created_at,
                updated_at=s_ipo.updated_at
            )
            tgt_db.add(new_ipo)
            ipo_inserted += 1

        tgt_db.commit()
        print(f"✅ IPOs: {ipo_inserted} inserted, {ipo_skipped} already existed.")

        # 4. Migrate IPO GMP records
        src_gmp = src_db.query(IPOGMP).order_by(IPOGMP.id).all()
        print(f"🔄 Migrating {len(src_gmp)} GMP time-series records...")
        gmp_inserted = 0
        gmp_skipped = 0

        for s_gmp in src_gmp:
            existing = tgt_db.query(IPOGMP).filter(IPOGMP.id == s_gmp.id).first()
            if existing:
                gmp_skipped += 1
                continue

            new_gmp = IPOGMP(
                id=s_gmp.id,
                ipo_id=s_gmp.ipo_id,
                gmp=s_gmp.gmp,
                estimated_listing_price=s_gmp.estimated_listing_price,
                estimated_gain_percent=s_gmp.estimated_gain_percent,
                kostak=s_gmp.kostak,
                subject_to_sauda=s_gmp.subject_to_sauda,
                source_name=s_gmp.source_name,
                source_url=s_gmp.source_url,
                recorded_at=s_gmp.recorded_at,
                created_at=s_gmp.created_at
            )
            tgt_db.add(new_gmp)
            gmp_inserted += 1

        tgt_db.commit()
        print(f"✅ GMP: {gmp_inserted} inserted, {gmp_skipped} already existed.")

        # 5. Migrate IPO Sources (Provenance)
        src_sources = src_db.query(IPOSource).order_by(IPOSource.id).all()
        print(f"🔄 Migrating {len(src_sources)} source provenance records...")
        src_inserted = 0
        src_skipped = 0

        for s_src in src_sources:
            existing = tgt_db.query(IPOSource).filter(IPOSource.id == s_src.id).first()
            if existing:
                src_skipped += 1
                continue

            new_src = IPOSource(
                id=s_src.id,
                ipo_id=s_src.ipo_id,
                source_name=s_src.source_name,
                source_url=s_src.source_url,
                source_ipo_id=s_src.source_ipo_id,
                raw_data=s_src.raw_data,
                fetched_at=s_src.fetched_at
            )
            tgt_db.add(new_src)
            src_inserted += 1

        tgt_db.commit()
        print(f"✅ Sources: {src_inserted} inserted, {src_skipped} already existed.")

        # 6. Migrate Source Health
        src_health = src_db.query(SourceHealth).all()
        print(f"🔄 Migrating {len(src_health)} source health records...")
        health_inserted = 0
        for s_h in src_health:
            existing = tgt_db.query(SourceHealth).filter(SourceHealth.source_id == s_h.source_id).first()
            if not existing:
                new_h = SourceHealth(
                    source_id=s_h.source_id,
                    source_name=s_h.source_name,
                    status=s_h.status,
                    last_successful_fetch=s_h.last_successful_fetch,
                    last_failed_fetch=s_h.last_failed_fetch,
                    records_returned=s_h.records_returned,
                    last_error_message=s_h.last_error_message,
                    updated_at=s_h.updated_at
                )
                tgt_db.add(new_h)
                health_inserted += 1
            else:
                existing.status = s_h.status
                existing.records_returned = s_h.records_returned
                existing.last_successful_fetch = s_h.last_successful_fetch
                existing.updated_at = s_h.updated_at

        tgt_db.commit()
        print(f"✅ Source Health: {health_inserted} inserted / updated.")

        # 7. Migrate Pipeline Runs
        src_runs = src_db.query(PipelineRun).order_by(PipelineRun.id).all()
        print(f"🔄 Migrating {len(src_runs)} pipeline run audit logs...")
        runs_inserted = 0
        for s_r in src_runs:
            existing = tgt_db.query(PipelineRun).filter(PipelineRun.id == s_r.id).first()
            if not existing:
                new_r = PipelineRun(
                    id=s_r.id,
                    started_at=s_r.started_at,
                    completed_at=s_r.completed_at,
                    status=s_r.status,
                    new_ipos_count=s_r.new_ipos_count,
                    updated_ipos_count=s_r.updated_ipos_count,
                    gmp_records_count=s_r.gmp_records_count,
                    conflicts_count=s_r.conflicts_count,
                    conflicts_summary=s_r.conflicts_summary,
                    sources_summary=s_r.sources_summary,
                    error_message=s_r.error_message
                )
                tgt_db.add(new_r)
                runs_inserted += 1

        tgt_db.commit()
        print(f"✅ Pipeline Runs: {runs_inserted} inserted.")

        # 8. Reset PostgreSQL SERIAL Sequences
        print("⚙️ Synchronizing PostgreSQL primary key sequences...")
        tables_to_sync = ["ipos", "ipo_gmp", "ipo_sources", "pipeline_runs"]
        with tgt_engine.connect() as conn:
            for tbl in tables_to_sync:
                try:
                    sync_sql = f"""
                    DO $$
                    DECLARE
                        seq_name text;
                        max_id bigint;
                    BEGIN
                        seq_name := pg_get_serial_sequence('{tbl}', 'id');
                        IF seq_name IS NOT NULL THEN
                            EXECUTE format('SELECT COALESCE(MAX(id), 1) FROM %I', '{tbl}') INTO max_id;
                            PERFORM setval(seq_name, max_id);
                        END IF;
                    END $$;
                    """
                    conn.execute(text(sync_sql))
                    conn.commit()
                except Exception as seq_err:
                    print(f"   ℹ️ Sequence sync note for {tbl}: {seq_err}")
        print("✅ Primary key sequences synchronized.")

        print("--------------------------------------------------------------------")
        print("🎉 MIGRATION TO POSTGRESQL COMPLETE!")
        print(f"   • Total Master IPOs:   {tgt_db.query(IPO).count()}")
        print(f"   • Total GMP Records:   {tgt_db.query(IPOGMP).count()}")
        print(f"   • Total Provenance:    {tgt_db.query(IPOSource).count()}")
        print(f"   • Source Health Rows:  {tgt_db.query(SourceHealth).count()}")
        print("====================================================================")

    except Exception as e:
        tgt_db.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        src_db.close()
        tgt_db.close()


if __name__ == "__main__":
    migrate()
