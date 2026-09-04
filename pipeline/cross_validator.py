import logging
import json
from typing import List, Dict, Any, Tuple, Optional
from slugify import slugify

from pipeline.models import NormalizedIPO, NormalizedGMP
from pipeline.validator import DataValidator
from pipeline.sources.base import BaseSourceAdapter

logger = logging.getLogger("ipodecoded.cross_validator")


class CrossValidator:
    """
    Cross-validates, resolves, and reconciles IPO and GMP data across multiple sources:
    1. Primary IPO Master: NSE (official exchange data takes precedence on dates/pricing)
    2. Secondary IPO Master: Chittorgarh (provides rich metadata: issue size, OFS, fresh issue, description)
    3. Primary GMP: InvestorGain (live grey market quotes)
    4. Secondary GMP: IPOWatch (independent live grey market quotes)

    Detects cross-source discrepancies and logs them without silently hiding conflicts.
    """

    @classmethod
    def get_canonical_key(cls, name: str, ipo_type: str = "Mainboard") -> str:
        clean = DataValidator.clean_company_name(name)
        return BaseSourceAdapter.generate_slug(clean, ipo_type)

    @classmethod
    def reconcile(
        cls,
        nse_items: List[NormalizedIPO],
        chittorgarh_items: List[NormalizedIPO],
        investorgain_items: List[NormalizedIPO],
        ipowatch_items: List[NormalizedIPO],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Reconciles data from all 4 sources into canonical entities.
        Returns:
            - reconciled_records: list of dicts with canonical IPO and metadata ready for upsert
            - all_conflicts: list of conflict dicts detected across sources
        """
        # Entity bucket map: canonical_slug -> dict of raw/normalized entries per source
        buckets: Dict[str, Dict[str, Any]] = {}

        def get_bucket(slug: str, ipo_type: str, company_name: str) -> Dict[str, Any]:
            if slug not in buckets:
                buckets[slug] = {
                    "slug": slug,
                    "ipo_type": ipo_type,
                    "company_name": company_name,
                    "nse": None,
                    "chittorgarh": None,
                    "investorgain": None,
                    "ipowatch": None,
                    "conflicts": [],
                    "sources_verified": set(),
                    "source_provenance": {}
                }
            return buckets[slug]

        # Helper for fuzzy matching if slug doesn't match exactly
        def find_existing_slug(clean_name: str, ipo_type: str) -> Optional[str]:
            target_slug = BaseSourceAdapter.generate_slug(clean_name, ipo_type)
            if target_slug in buckets:
                return target_slug
            
            # Check prefix / token match
            name_tokens = set(re_tokens(clean_name))
            if len(name_tokens) >= 2:
                for existing_slug, b in buckets.items():
                    if b["ipo_type"] == ipo_type:
                        existing_tokens = set(re_tokens(b["company_name"]))
                        if len(existing_tokens) >= 2:
                            # Intersection
                            common = name_tokens.intersection(existing_tokens)
                            if len(common) >= min(len(name_tokens), len(existing_tokens)):
                                return existing_slug
            return None

        # 1. Bucket NSE Items (Official Exchange Data)
        for item in nse_items:
            slug = cls.get_canonical_key(item.company_name, item.ipo_type)
            b = get_bucket(slug, item.ipo_type, item.company_name)
            b["nse"] = item
            b["sources_verified"].add("NSE")
            b["source_provenance"]["NSE"] = {
                "source_name": "NSE",
                "source_url": item.source_url,
                "source_ipo_id": item.source_id or item.symbol,
                "raw_data": item.raw_data
            }

        # 2. Bucket Chittorgarh Items (Secondary Master Aggregator)
        for item in chittorgarh_items:
            matched_slug = find_existing_slug(item.company_name, item.ipo_type)
            slug = matched_slug or cls.get_canonical_key(item.company_name, item.ipo_type)
            b = get_bucket(slug, item.ipo_type, item.company_name)
            b["chittorgarh"] = item
            b["sources_verified"].add("Chittorgarh")
            b["source_provenance"]["Chittorgarh"] = {
                "source_name": "Chittorgarh",
                "source_url": item.source_url,
                "source_ipo_id": item.source_id or item.slug,
                "raw_data": item.raw_data
            }

        # 3. Bucket InvestorGain Items (Primary Live GMP)
        for item in investorgain_items:
            matched_slug = find_existing_slug(item.company_name, item.ipo_type)
            slug = matched_slug or cls.get_canonical_key(item.company_name, item.ipo_type)
            b = get_bucket(slug, item.ipo_type, item.company_name)
            b["investorgain"] = item
            b["sources_verified"].add("InvestorGain")
            b["source_provenance"]["InvestorGain"] = {
                "source_name": "InvestorGain",
                "source_url": item.source_url,
                "source_ipo_id": item.source_id or item.slug,
                "raw_data": item.raw_data
            }

        # 4. Bucket IPOWatch Items (Secondary Live GMP)
        for item in ipowatch_items:
            matched_slug = find_existing_slug(item.company_name, item.ipo_type)
            slug = matched_slug or cls.get_canonical_key(item.company_name, item.ipo_type)
            b = get_bucket(slug, item.ipo_type, item.company_name)
            b["ipowatch"] = item
            b["sources_verified"].add("IPOWatch")
            b["source_provenance"]["IPOWatch"] = {
                "source_name": "IPOWatch",
                "source_url": item.source_url,
                "source_ipo_id": item.source_id or item.slug,
                "raw_data": item.raw_data
            }

        reconciled_records: List[Dict[str, Any]] = []
        all_conflicts: List[Dict[str, Any]] = []

        # Reconcile each entity
        for slug, b in buckets.items():
            conflicts: List[Dict[str, Any]] = []
            nse: Optional[NormalizedIPO] = b["nse"]
            chit: Optional[NormalizedIPO] = b["chittorgarh"]
            ig: Optional[NormalizedIPO] = b["investorgain"]
            iw: Optional[NormalizedIPO] = b["ipowatch"]

            # Choose base canonical IPO: NSE preferred, then Chittorgarh, then IG, then IW
            base = nse or chit or ig or iw
            if not base:
                continue

            company_name = (nse.company_name if nse else (chit.company_name if chit else base.company_name))
            ipo_type = base.ipo_type

            # Canonical record construction
            canonical = NormalizedIPO(
                company_name=company_name,
                slug=slug,
                ipo_type=ipo_type,
                status=base.status,
                open_date=base.open_date,
                close_date=base.close_date,
                allotment_date=base.allotment_date,
                listing_date=base.listing_date,
                price_band_low=base.price_band_low,
                price_band_high=base.price_band_high,
                lot_size=base.lot_size,
                minimum_investment=base.minimum_investment,
                issue_size=base.issue_size,
                fresh_issue=base.fresh_issue,
                ofs=base.ofs,
                face_value=base.face_value,
                subscription_status=base.subscription_status,
                subscription_retail=base.subscription_retail,
                subscription_qib=base.subscription_qib,
                subscription_nii=base.subscription_nii,
                subscription_total=base.subscription_total,
                company_description=base.company_description,
                symbol=base.symbol,
                source_name=base.source_name,
                source_url=base.source_url,
                source_id=base.source_id
            )

            # Master data field-level reconciliation & conflict detection (NSE vs Chittorgarh)
            if nse and chit:
                # 1. Open Date Conflict
                if nse.open_date and chit.open_date and nse.open_date != chit.open_date:
                    conf = {
                        "ipo_slug": slug,
                        "company_name": company_name,
                        "field": "open_date",
                        "source_1": "NSE",
                        "val_1": nse.open_date.isoformat(),
                        "source_2": "Chittorgarh",
                        "val_2": chit.open_date.isoformat(),
                        "resolved_to": nse.open_date.isoformat(),
                        "resolution": "NSE_OFFICIAL_PRECEDENCE"
                    }
                    conflicts.append(conf)
                    all_conflicts.append(conf)
                    canonical.open_date = nse.open_date
                elif chit.open_date and not nse.open_date:
                    canonical.open_date = chit.open_date

                # 2. Close Date Conflict
                if nse.close_date and chit.close_date and nse.close_date != chit.close_date:
                    conf = {
                        "ipo_slug": slug,
                        "company_name": company_name,
                        "field": "close_date",
                        "source_1": "NSE",
                        "val_1": nse.close_date.isoformat(),
                        "source_2": "Chittorgarh",
                        "val_2": chit.close_date.isoformat(),
                        "resolved_to": nse.close_date.isoformat(),
                        "resolution": "NSE_OFFICIAL_PRECEDENCE"
                    }
                    conflicts.append(conf)
                    all_conflicts.append(conf)
                    canonical.close_date = nse.close_date
                elif chit.close_date and not nse.close_date:
                    canonical.close_date = chit.close_date

                # 3. Price Band Conflict
                if nse.price_band_high and chit.price_band_high:
                    if (nse.price_band_high != chit.price_band_high) or (nse.price_band_low != chit.price_band_low):
                        conf = {
                            "ipo_slug": slug,
                            "company_name": company_name,
                            "field": "price_band",
                            "source_1": "NSE",
                            "val_1": f"{nse.price_band_low}-{nse.price_band_high}",
                            "source_2": "Chittorgarh",
                            "val_2": f"{chit.price_band_low}-{chit.price_band_high}",
                            "resolved_to": f"{nse.price_band_low}-{nse.price_band_high}",
                            "resolution": "NSE_OFFICIAL_PRECEDENCE"
                        }
                        conflicts.append(conf)
                        all_conflicts.append(conf)
                        canonical.price_band_low = nse.price_band_low
                        canonical.price_band_high = nse.price_band_high
                elif chit.price_band_high and not nse.price_band_high:
                    canonical.price_band_low = chit.price_band_low
                    canonical.price_band_high = chit.price_band_high

                # Enrich with Chittorgarh rich secondary metadata if missing in NSE
                if not canonical.issue_size and chit.issue_size:
                    canonical.issue_size = chit.issue_size
                if not canonical.fresh_issue and chit.fresh_issue:
                    canonical.fresh_issue = chit.fresh_issue
                if not canonical.ofs and chit.ofs:
                    canonical.ofs = chit.ofs
                if not canonical.listing_date and chit.listing_date:
                    canonical.listing_date = chit.listing_date
                if not canonical.company_description and chit.company_description:
                    canonical.company_description = chit.company_description
                if not canonical.lot_size and chit.lot_size:
                    canonical.lot_size = chit.lot_size
                if not canonical.minimum_investment and chit.minimum_investment:
                    canonical.minimum_investment = chit.minimum_investment

            elif chit and not nse:
                # Chittorgarh is master
                canonical.open_date = chit.open_date
                canonical.close_date = chit.close_date
                canonical.listing_date = chit.listing_date
                canonical.price_band_low = chit.price_band_low
                canonical.price_band_high = chit.price_band_high
                canonical.issue_size = chit.issue_size
                canonical.fresh_issue = chit.fresh_issue
                canonical.ofs = chit.ofs
                canonical.company_description = chit.company_description
                canonical.status = chit.status

            # Fill missing dates/pricing from InvestorGain if still missing
            if ig:
                if not canonical.open_date and ig.open_date:
                    canonical.open_date = ig.open_date
                if not canonical.close_date and ig.close_date:
                    canonical.close_date = ig.close_date
                if not canonical.allotment_date and ig.allotment_date:
                    canonical.allotment_date = ig.allotment_date
                if not canonical.listing_date and ig.listing_date:
                    canonical.listing_date = ig.listing_date
                if not canonical.price_band_high and ig.price_band_high:
                    canonical.price_band_low = ig.price_band_low
                    canonical.price_band_high = ig.price_band_high
                if not canonical.lot_size and ig.lot_size:
                    canonical.lot_size = ig.lot_size
                if not canonical.issue_size and ig.issue_size:
                    canonical.issue_size = ig.issue_size

            # 1. Deterministic Status Derivation based on official issue timetable
            from datetime import date
            today = date.today()
            if canonical.listing_date and today >= canonical.listing_date:
                canonical.status = "Listed"
            elif canonical.close_date and today > canonical.close_date:
                canonical.status = "Closed"
            elif canonical.open_date and canonical.close_date and canonical.open_date <= today <= canonical.close_date:
                canonical.status = "Open"
            elif canonical.open_date and today < canonical.open_date:
                canonical.status = "Upcoming"
            elif base.status in ["Open", "Upcoming", "Closed", "Listed"]:
                canonical.status = base.status
            else:
                canonical.status = "Upcoming"

            # 2. Master Data Validation Semantics
            master_sources = [s for s in ["NSE", "Chittorgarh"] if s in b["sources_verified"]]
            master_data_validated = ("NSE" in master_sources) or (len(master_sources) >= 2)
            if not master_data_validated and chit and (chit.open_date or chit.listing_date):
                master_data_validated = True

            # 3. GMP Provenance & Independent Dual Quotes
            # - Primary GMP is always InvestorGain
            # - Secondary GMP is always IPOWatch
            # - Neither value overwrites the other
            # - spread_low = min(InvestorGain, IPOWatch)
            # - spread_high = max(InvestorGain, IPOWatch)
            ig_gmp_obj: Optional[NormalizedGMP] = ig.current_gmp if ig else None
            iw_gmp_obj: Optional[NormalizedGMP] = iw.current_gmp if iw else None

            ig_val = float(ig_gmp_obj.gmp) if (ig_gmp_obj and ig_gmp_obj.gmp is not None) else None
            iw_val = float(iw_gmp_obj.gmp) if (iw_gmp_obj and iw_gmp_obj.gmp is not None) else None

            gmp_sources_available = (ig_val is not None) or (iw_val is not None)
            gmp_divergence_alert = False
            spread_low = None
            spread_high = None
            gmp_spread = None

            if ig_val is not None and iw_val is not None:
                spread_low = min(ig_val, iw_val)
                spread_high = max(ig_val, iw_val)
                gmp_spread = f"₹{spread_low:.0f} – ₹{spread_high:.0f}" if spread_low != spread_high else f"₹{spread_low:.0f}"

                max_val = max(abs(ig_val), abs(iw_val))
                if max_val > 0:
                    divergence_pct = (abs(ig_val - iw_val) / max_val) * 100
                    if divergence_pct > 30.0:
                        gmp_divergence_alert = True
                        conf = {
                            "ipo_slug": slug,
                            "company_name": company_name,
                            "field": "gmp_divergence",
                            "source_1": "InvestorGain",
                            "val_1": ig_val,
                            "source_2": "IPOWatch",
                            "val_2": iw_val,
                            "divergence_percent": round(divergence_pct, 1),
                            "resolved_to": gmp_spread,
                            "resolution": "RECORDED_SPREAD"
                        }
                        conflicts.append(conf)
                        all_conflicts.append(conf)

            elif ig_val is not None and iw_val is None:
                spread_low = ig_val
                spread_high = ig_val
                gmp_spread = f"₹{ig_val:.0f}"

            elif iw_val is not None and ig_val is None:
                spread_low = iw_val
                spread_high = iw_val
                gmp_spread = f"₹{iw_val:.0f}"

            # Canonical primary GMP quote preference: InvestorGain (primary), fallback to IPOWatch if IG missing
            canonical.current_gmp = ig_gmp_obj if ig_gmp_obj is not None else iw_gmp_obj

            sources_list = sorted(list(b["sources_verified"]))
            is_cross_val = bool(master_data_validated and len(sources_list) >= 2)
            has_conflicts = len(conflicts) > 0

            reconciled_records.append({
                "canonical": canonical,
                "gmp_investorgain": ig_val,
                "gmp_ipowatch": iw_val,
                "current_gmp_secondary": iw_val,
                "gmp_spread": gmp_spread,
                "gmp_spread_low": spread_low,
                "gmp_spread_high": spread_high,
                "master_data_validated": master_data_validated,
                "gmp_sources_available": gmp_sources_available,
                "gmp_divergence_alert": gmp_divergence_alert,
                "is_cross_validated": is_cross_val,
                "has_conflicts": has_conflicts,
                "conflicts": conflicts,
                "sources_verified": sources_list,
                "source_provenance": b["source_provenance"],
                "gmp_records_to_save": [g for g in [ig_gmp_obj, iw_gmp_obj] if g is not None]
            })

        logger.info(f"Reconciled {len(reconciled_records)} IPO entities across sources. Detected {len(all_conflicts)} conflicts.")
        return reconciled_records, all_conflicts


def re_tokens(text: str) -> List[str]:
    import re
    return [t.lower() for t in re.findall(r'[a-zA-Z0-9]+', text) if len(t) > 2]
