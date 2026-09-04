import logging
import sys
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.db import SessionLocal, init_db, IPO, IPOGMP, SourceHealth, PipelineRun
from pipeline.sources.nse_adapter import NSEAdapter
from pipeline.sources.chittorgarh_adapter import ChittorgarhAdapter
from pipeline.sources.investorgain_adapter import InvestorGainAdapter
from pipeline.sources.ipowatch_adapter import IPOWatchAdapter
from pipeline.cross_validator import CrossValidator
from pipeline.upsert import upsert_reconciled_ipo
from pipeline.models import NormalizedIPO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ipodecoded.pipeline")


def update_source_health(
    db: Session,
    source_id: str,
    source_name: str,
    status: str,
    records_count: int,
    error_msg: Optional[str] = None
):
    """
    Updates or inserts the source health record in the source_health table.
    """
    now_utc = datetime.now(timezone.utc)
    health = db.query(SourceHealth).filter(SourceHealth.source_id == source_id).first()
    if not health:
        health = SourceHealth(
            source_id=source_id,
            source_name=source_name,
            status=status,
            records_returned=records_count,
            last_successful_fetch=now_utc if status == "HEALTHY" else None,
            last_failed_fetch=now_utc if status == "FAILED" else None,
            last_error_message=error_msg,
            updated_at=now_utc
        )
        db.add(health)
    else:
        health.status = status
        health.records_returned = records_count
        if status == "HEALTHY":
            health.last_successful_fetch = now_utc
            health.last_error_message = None
        else:
            health.last_failed_fetch = now_utc
            health.last_error_message = error_msg
        health.updated_at = now_utc


def run_pipeline(db: Session = None) -> Dict[str, Any]:
    """
    Executes a complete cycle of the multi-source live IPO and GMP data pipeline:
    1. Fetches from official exchange (NSE) and aggregator (Chittorgarh) for master data.
    2. Fetches independent live GMP from InvestorGain and IPOWatch.
    3. NO seed/synthetic fallback - only genuine live market data is processed.
    4. Reconciles entities and cross-validates data, logging conflicts explicitly.
    5. Saves full source provenance, timestamps, and time-series GMP observations.
    6. If all sources fail, makes zero database changes and preserves existing state.
    """
    close_db = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_db = True

    start_time = datetime.now(timezone.utc)
    summary: Dict[str, Any] = {
        "timestamp": start_time.isoformat(),
        "status": "RUNNING",
        "sources": {},
        "records_fetched": {},
        "total_extracted": 0,
        "new_ipos": 0,
        "updated_ipos": 0,
        "gmp_records_added": 0,
        "conflicts_count": 0,
        "conflicts": [],
        "errors": []
    }

    try:
        logger.info("==================================================")
        logger.info("STARTING MULTI-SOURCE LIVE IPO & GMP INGESTION CYCLE")
        logger.info("==================================================")

        # 1. Fetch from NSE Adapter (Primary / Official Master)
        nse_ipos: List[NormalizedIPO] = []
        nse = NSEAdapter()
        try:
            nse_ipos = nse.fetch_and_parse()
            nse_status = "HEALTHY" if len(nse_ipos) > 0 else "DEGRADED"
            summary["sources"]["nse"] = {"name": nse.name, "status": nse_status, "count": len(nse_ipos)}
            summary["records_fetched"]["NSE"] = len(nse_ipos)
            update_source_health(db, "nse", nse.name, nse_status, len(nse_ipos))
            logger.info(f"[NSE] Successfully fetched {len(nse_ipos)} live IPO records.")
        except Exception as e:
            logger.error(f"[NSE] Fetch failed: {e}")
            summary["sources"]["nse"] = {"name": nse.name, "status": "FAILED", "count": 0, "error": str(e)}
            summary["records_fetched"]["NSE"] = 0
            summary["errors"].append(f"NSE: {str(e)}")
            update_source_health(db, "nse", nse.name, "FAILED", 0, str(e))

        # 2. Fetch from Chittorgarh Adapter (Secondary Master / Rich Metadata)
        chittorgarh_ipos: List[NormalizedIPO] = []
        chit = ChittorgarhAdapter()
        try:
            chittorgarh_ipos = chit.fetch_and_parse()
            chit_status = "HEALTHY" if len(chittorgarh_ipos) > 0 else "DEGRADED"
            summary["sources"]["chittorgarh"] = {"name": chit.name, "status": chit_status, "count": len(chittorgarh_ipos)}
            summary["records_fetched"]["Chittorgarh"] = len(chittorgarh_ipos)
            update_source_health(db, "chittorgarh", chit.name, chit_status, len(chittorgarh_ipos))
            logger.info(f"[Chittorgarh] Successfully fetched {len(chittorgarh_ipos)} live IPO records.")
        except Exception as e:
            logger.error(f"[Chittorgarh] Fetch failed: {e}")
            summary["sources"]["chittorgarh"] = {"name": chit.name, "status": "FAILED", "count": 0, "error": str(e)}
            summary["records_fetched"]["Chittorgarh"] = 0
            summary["errors"].append(f"Chittorgarh: {str(e)}")
            update_source_health(db, "chittorgarh", chit.name, "FAILED", 0, str(e))

        # 3. Fetch from InvestorGain Adapter (Primary Live GMP)
        investorgain_ipos: List[NormalizedIPO] = []
        ig = InvestorGainAdapter()
        try:
            investorgain_ipos = ig.fetch_and_parse()
            ig_status = "HEALTHY" if len(investorgain_ipos) > 0 else "DEGRADED"
            summary["sources"]["investorgain"] = {"name": ig.name, "status": ig_status, "count": len(investorgain_ipos)}
            summary["records_fetched"]["InvestorGain"] = len(investorgain_ipos)
            update_source_health(db, "investorgain", ig.name, ig_status, len(investorgain_ipos))
            logger.info(f"[InvestorGain] Successfully fetched {len(investorgain_ipos)} live GMP records.")
        except Exception as e:
            logger.error(f"[InvestorGain] Fetch failed: {e}")
            summary["sources"]["investorgain"] = {"name": ig.name, "status": "FAILED", "count": 0, "error": str(e)}
            summary["records_fetched"]["InvestorGain"] = 0
            summary["errors"].append(f"InvestorGain: {str(e)}")
            update_source_health(db, "investorgain", ig.name, "FAILED", 0, str(e))

        # 4. Fetch from IPOWatch Adapter (Secondary Independent Live GMP)
        ipowatch_ipos: List[NormalizedIPO] = []
        iw = IPOWatchAdapter()
        try:
            ipowatch_ipos = iw.fetch_and_parse()
            iw_status = "HEALTHY" if len(ipowatch_ipos) > 0 else "DEGRADED"
            summary["sources"]["ipowatch"] = {"name": iw.name, "status": iw_status, "count": len(ipowatch_ipos)}
            summary["records_fetched"]["IPOWatch"] = len(ipowatch_ipos)
            update_source_health(db, "ipowatch", iw.name, iw_status, len(ipowatch_ipos))
            logger.info(f"[IPOWatch] Successfully fetched {len(ipowatch_ipos)} live GMP records.")
        except Exception as e:
            logger.error(f"[IPOWatch] Fetch failed: {e}")
            summary["sources"]["ipowatch"] = {"name": iw.name, "status": "FAILED", "count": 0, "error": str(e)}
            summary["records_fetched"]["IPOWatch"] = 0
            summary["errors"].append(f"IPOWatch: {str(e)}")
            update_source_health(db, "ipowatch", iw.name, "FAILED", 0, str(e))

        total_extracted = len(nse_ipos) + len(chittorgarh_ipos) + len(investorgain_ipos) + len(ipowatch_ipos)
        summary["total_extracted"] = total_extracted

        # Resilience Rule: If ALL sources fail / return 0, commit zero changes and preserve state
        if total_extracted == 0:
            err_msg = "CRITICAL: All 4 data sources failed or returned zero records. Preserving last valid database state with zero modifications."
            logger.error(err_msg)
            summary["status"] = "FAILED"
            summary["errors"].append(err_msg)

            # Record failed pipeline run
            run_rec = PipelineRun(
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                status="FAILED",
                new_ipos_count=0,
                updated_ipos_count=0,
                gmp_records_count=0,
                conflicts_count=0,
                sources_summary=json.dumps(summary["sources"]),
                error_message=err_msg
            )
            db.add(run_rec)
            db.commit()
            return summary

        # 5. Cross-Validation and Reconciliation Engine
        logger.info("Reconciling and cross-validating records across sources...")
        reconciled_items, conflicts = CrossValidator.reconcile(
            nse_items=nse_ipos,
            chittorgarh_items=chittorgarh_ipos,
            investorgain_items=investorgain_ipos,
            ipowatch_items=ipowatch_ipos
        )

        summary["conflicts_count"] = len(conflicts)
        summary["conflicts"] = conflicts

        # 6. Upsert Reconciled IPOs and Persist Provenance & GMP Time-Series
        for item in reconciled_items:
            try:
                ipo_obj, is_new, is_updated, gmp_added = upsert_reconciled_ipo(db, item)
                if is_new:
                    summary["new_ipos"] += 1
                elif is_updated:
                    summary["updated_ipos"] += 1
                summary["gmp_records_added"] += gmp_added
            except Exception as e:
                canonical = item.get("canonical")
                c_name = canonical.company_name if canonical else "Unknown"
                logger.error(f"Error upserting reconciled IPO '{c_name}': {e}")
                summary["errors"].append(f"Upsert error for {c_name}: {str(e)}")

        end_time = datetime.now(timezone.utc)
        overall_status = "DEGRADED" if len(summary["errors"]) > 0 else "SUCCESS"
        summary["status"] = overall_status

        # 7. Record Pipeline Run Log
        pipeline_run = PipelineRun(
            started_at=start_time,
            completed_at=end_time,
            status=overall_status,
            new_ipos_count=summary["new_ipos"],
            updated_ipos_count=summary["updated_ipos"],
            gmp_records_count=summary["gmp_records_added"],
            conflicts_count=summary["conflicts_count"],
            conflicts_summary=json.dumps(conflicts),
            sources_summary=json.dumps(summary["sources"]),
            error_message="; ".join(summary["errors"]) if summary["errors"] else None
        )
        db.add(pipeline_run)
        db.commit()

        logger.info("==================================================")
        logger.info(
            f"MULTI-SOURCE CYCLE COMPLETE: {summary['new_ipos']} new IPOs, "
            f"{summary['updated_ipos']} updated IPOs, "
            f"{summary['gmp_records_added']} GMP observations recorded, "
            f"{summary['conflicts_count']} cross-source conflicts logged."
        )
        logger.info("==================================================")
        return summary

    except Exception as e:
        db.rollback()
        logger.error(f"Critical unhandled exception in pipeline runner: {e}")
        summary["status"] = "FAILED"
        summary["errors"].append(str(e))
        return summary
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    result = run_pipeline()
    print(json.dumps(result, indent=2, default=str))
