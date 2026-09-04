import logging
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session
from backend.db import IPO, IPOGMP, IPOSource
from pipeline.models import NormalizedIPO, NormalizedGMP
from pipeline.validator import DataValidator

logger = logging.getLogger("ipodecoded.upsert")


def safe_update_field(existing_val: Any, new_val: Any) -> Tuple[Any, bool]:
    """
    Safely checks if a field should be updated.
    Rule: Never overwrite an existing valid non-null value with None or empty string!
    Returns (new_value_to_persist, has_changed).
    """
    if new_val is None:
        return existing_val, False

    if isinstance(new_val, str) and not new_val.strip():
        return existing_val, False

    # Handle float vs Decimal comparison
    if isinstance(existing_val, Decimal) and isinstance(new_val, (float, int)):
        if round(float(existing_val), 4) == round(float(new_val), 4):
            return existing_val, False

    # Compare values
    if existing_val != new_val:
        return new_val, True

    return existing_val, False


def upsert_ipo(db: Session, ipo_data: NormalizedIPO) -> Tuple[Optional[IPO], bool, bool]:
    """
    Idempotent upsert for an IPO record.
    Returns: (ipo_instance, is_created, is_updated)
    """
    if not DataValidator.validate_ipo(ipo_data):
        logger.warning(f"Validation failed for IPO '{ipo_data.company_name}'. Skipping.")
        return None, False, False

    # Find existing record by slug
    existing = db.query(IPO).filter(IPO.slug == ipo_data.slug).first()

    if not existing:
        # Fallback: check by normalized company name + ipo_type
        existing = db.query(IPO).filter(
            IPO.company_name.ilike(ipo_data.company_name.strip()),
            IPO.ipo_type == ipo_data.ipo_type
        ).first()

    now_utc = datetime.now(timezone.utc)

    if not existing:
        # Insert brand new IPO
        new_ipo = IPO(
            company_name=ipo_data.company_name,
            slug=ipo_data.slug,
            ipo_type=ipo_data.ipo_type,
            status=ipo_data.status,
            open_date=ipo_data.open_date,
            close_date=ipo_data.close_date,
            allotment_date=ipo_data.allotment_date,
            refund_date=ipo_data.refund_date,
            demat_date=ipo_data.demat_date,
            listing_date=ipo_data.listing_date,
            price_band_low=ipo_data.price_band_low,
            price_band_high=ipo_data.price_band_high,
            lot_size=ipo_data.lot_size,
            minimum_investment=ipo_data.minimum_investment,
            issue_size=ipo_data.issue_size,
            fresh_issue=ipo_data.fresh_issue,
            ofs=ipo_data.ofs,
            face_value=ipo_data.face_value,
            subscription_status=ipo_data.subscription_status,
            subscription_retail=ipo_data.subscription_retail,
            subscription_qib=ipo_data.subscription_qib,
            subscription_nii=ipo_data.subscription_nii,
            subscription_total=ipo_data.subscription_total,
            company_description=ipo_data.company_description,
            source_name=ipo_data.source_name,
            source_url=ipo_data.source_url,
            source_id=ipo_data.source_id,
            created_at=now_utc,
            updated_at=now_utc
        )
        db.add(new_ipo)
        db.flush()
        logger.info(f"[NEW] Created IPO record: '{new_ipo.company_name}' ({new_ipo.slug})")

        # Insert initial GMP if provided
        if ipo_data.current_gmp:
            upsert_gmp(db, new_ipo, ipo_data.current_gmp)

        return new_ipo, True, False

    # Existing IPO found -> Perform Change Detection
    changed = False
    fields_to_check = [
        "status", "open_date", "close_date", "allotment_date", "refund_date",
        "demat_date", "listing_date", "price_band_low", "price_band_high",
        "lot_size", "minimum_investment", "issue_size", "fresh_issue",
        "ofs", "face_value", "subscription_status", "subscription_retail",
        "subscription_qib", "subscription_nii", "subscription_total",
        "company_description", "source_name", "source_url"
    ]

    for field in fields_to_check:
        old_val = getattr(existing, field)
        new_val = getattr(ipo_data, field)
        val_to_set, is_field_changed = safe_update_field(old_val, new_val)
        if is_field_changed:
            setattr(existing, field, val_to_set)
            changed = True
            logger.info(f"[UPDATE] IPO '{existing.company_name}' {field}: '{old_val}' -> '{val_to_set}'")

    if changed:
        existing.updated_at = now_utc
        db.flush()
        logger.info(f"[UPDATED] IPO record '{existing.company_name}' refreshed.")

    # Process GMP update if present
    if ipo_data.current_gmp:
        upsert_gmp(db, existing, ipo_data.current_gmp)

    return existing, False, changed


def upsert_ipo_sources(db: Session, ipo_id: int, source_provenance: Dict[str, Dict[str, Any]]):
    """
    Saves or updates source audit entries in the ipo_sources table.
    """
    now_utc = datetime.now(timezone.utc)
    for source_name, p_data in source_provenance.items():
        existing_src = db.query(IPOSource).filter(
            IPOSource.ipo_id == ipo_id,
            IPOSource.source_name == source_name
        ).first()

        raw_json = json.dumps(p_data.get("raw_data"), default=str) if p_data.get("raw_data") is not None else None
        if existing_src:
            existing_src.source_url = p_data.get("source_url") or existing_src.source_url
            existing_src.source_ipo_id = p_data.get("source_ipo_id") or existing_src.source_ipo_id
            if raw_json:
                existing_src.raw_data = raw_json
            existing_src.fetched_at = now_utc
        else:
            new_src = IPOSource(
                ipo_id=ipo_id,
                source_name=source_name,
                source_url=p_data.get("source_url"),
                source_ipo_id=p_data.get("source_ipo_id"),
                raw_data=raw_json,
                fetched_at=now_utc
            )
            db.add(new_src)


def upsert_reconciled_ipo(db: Session, item: Dict[str, Any]) -> Tuple[Optional[IPO], bool, bool, int]:
    """
    Upserts a cross-validated, reconciled IPO record with multi-source metadata:
    1. Upserts the canonical IPO
    2. Updates cross-validation flags, spread, and conflicts
    3. Persists provenance into ipo_sources table
    4. Persists time-series GMP observations into ipo_gmp table
    Returns: (ipo_instance, is_created, is_updated, gmp_added_count)
    """
    canonical: NormalizedIPO = item["canonical"]
    ipo_obj, is_created, is_updated = upsert_ipo(db, canonical)
    if not ipo_obj:
        return None, False, False, 0

    now_utc = datetime.now(timezone.utc)
    meta_changed = False

    # Update validation semantics & conflict attributes
    is_cross_val = item.get("is_cross_validated", False)
    master_val = item.get("master_data_validated", False)
    gmp_avail = item.get("gmp_sources_available", False)
    gmp_div = item.get("gmp_divergence_alert", False)
    has_conflicts = item.get("has_conflicts", False)
    conflicts_json = json.dumps(item.get("conflicts", [])) if item.get("conflicts") else None
    sources_verified_json = json.dumps(item.get("sources_verified", [])) if item.get("sources_verified") else None

    ig_gmp = item.get("gmp_investorgain")
    iw_gmp = item.get("gmp_ipowatch")
    sec_gmp = item.get("current_gmp_secondary")
    gmp_spread = item.get("gmp_spread")
    spread_low = item.get("gmp_spread_low")
    spread_high = item.get("gmp_spread_high")
    canonical_status = canonical.status

    if ipo_obj.status != canonical_status:
        ipo_obj.status = canonical_status
        meta_changed = True

    if ipo_obj.master_data_validated != master_val:
        ipo_obj.master_data_validated = master_val
        meta_changed = True

    if ipo_obj.gmp_sources_available != gmp_avail:
        ipo_obj.gmp_sources_available = gmp_avail
        meta_changed = True

    if ipo_obj.gmp_divergence_alert != gmp_div:
        ipo_obj.gmp_divergence_alert = gmp_div
        meta_changed = True

    if ipo_obj.is_cross_validated != is_cross_val:
        ipo_obj.is_cross_validated = is_cross_val
        meta_changed = True

    if ipo_obj.has_conflicts != has_conflicts:
        ipo_obj.has_conflicts = has_conflicts
        meta_changed = True

    if ipo_obj.conflicts_json != conflicts_json:
        ipo_obj.conflicts_json = conflicts_json
        meta_changed = True

    if ipo_obj.sources_verified != sources_verified_json:
        ipo_obj.sources_verified = sources_verified_json
        meta_changed = True

    if safe_update_field(ipo_obj.gmp_investorgain, ig_gmp)[1]:
        ipo_obj.gmp_investorgain = ig_gmp
        meta_changed = True

    if safe_update_field(ipo_obj.gmp_ipowatch, iw_gmp)[1]:
        ipo_obj.gmp_ipowatch = iw_gmp
        meta_changed = True

    if safe_update_field(ipo_obj.current_gmp_secondary, sec_gmp)[1]:
        ipo_obj.current_gmp_secondary = sec_gmp
        meta_changed = True

    if safe_update_field(ipo_obj.gmp_spread, gmp_spread)[1]:
        ipo_obj.gmp_spread = gmp_spread
        meta_changed = True

    if safe_update_field(ipo_obj.gmp_spread_low, spread_low)[1]:
        ipo_obj.gmp_spread_low = spread_low
        meta_changed = True

    if safe_update_field(ipo_obj.gmp_spread_high, spread_high)[1]:
        ipo_obj.gmp_spread_high = spread_high
        meta_changed = True

    if meta_changed:
        ipo_obj.updated_at = now_utc
        db.flush()

    # Provenance auditing
    source_prov = item.get("source_provenance", {})
    if source_prov:
        upsert_ipo_sources(db, ipo_obj.id, source_prov)

    # GMP history tracking for all available GMP quotes
    gmp_added_count = 0
    gmp_records_to_save: List[NormalizedGMP] = item.get("gmp_records_to_save", [])
    for gmp_rec in gmp_records_to_save:
        _, gmp_created = upsert_gmp(db, ipo_obj, gmp_rec)
        if gmp_created:
            gmp_added_count += 1

    return ipo_obj, is_created, is_updated, gmp_added_count


def upsert_gmp(db: Session, ipo: IPO, gmp_data: NormalizedGMP) -> Tuple[Optional[IPOGMP], bool]:
    """
    Idempotent GMP tracking with History Preservation:
    1. Check the most recent GMP recorded for this IPO from this specific source.
    2. If latest GMP == new GMP, do NOT create a duplicate record.
    3. If latest GMP != new GMP (or no previous GMP exists), insert a new historical record!
    Returns (gmp_instance, is_new_record_created)
    """
    pb_high = float(ipo.price_band_high) if ipo.price_band_high else None
    if not DataValidator.validate_gmp(gmp_data, pb_high):
        return None, False

    now_utc = datetime.now(timezone.utc)
    rec_time = gmp_data.recorded_at or now_utc

    # Check latest recorded GMP for this specific source
    latest_gmp = db.query(IPOGMP).filter(
        IPOGMP.ipo_id == ipo.id,
        IPOGMP.source_name == gmp_data.source_name
    ).order_by(IPOGMP.recorded_at.desc()).first()

    # If GMP hasn't changed for this source on the same calendar day, avoid duplicate
    if latest_gmp:
        latest_date = latest_gmp.recorded_at.date() if hasattr(latest_gmp.recorded_at, 'date') else None
        rec_date = rec_time.date() if hasattr(rec_time, 'date') else None
        if latest_date and rec_date and latest_date == rec_date and float(latest_gmp.gmp) == float(gmp_data.gmp):
            return latest_gmp, False
    new_record = IPOGMP(
        ipo_id=ipo.id,
        gmp=gmp_data.gmp,
        estimated_listing_price=gmp_data.estimated_listing_price,
        estimated_gain_percent=gmp_data.estimated_gain_percent,
        kostak=gmp_data.kostak,
        subject_to_sauda=gmp_data.subject_to_sauda,
        source_name=gmp_data.source_name,
        source_url=gmp_data.source_url,
        recorded_at=gmp_data.recorded_at or now_utc,
        created_at=now_utc
    )
    db.add(new_record)
    db.flush()

    ipo.updated_at = now_utc
    prev_val = latest_gmp.gmp if latest_gmp else 'None'
    logger.info(f"[GMP UPDATE] IPO '{ipo.company_name}': [{gmp_data.source_name}] Previous GMP={prev_val}, New GMP={gmp_data.gmp}")
    return new_record, True
