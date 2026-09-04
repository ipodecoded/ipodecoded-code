import re
import logging
import httpx
from typing import List, Optional
from bs4 import BeautifulSoup
from datetime import datetime, timezone, date
from pipeline.sources.base import BaseSourceAdapter
from pipeline.models import NormalizedIPO, NormalizedGMP
from pipeline.validator import DataValidator
from backend.config import SCRAPER_USER_AGENT, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger("ipodecoded.sources.investorgain")

class InvestorGainAdapter(BaseSourceAdapter):
    name: str = "InvestorGain"
    base_url: str = "https://www.investorgain.com"

    API_DATA_URL = "https://webnodejs.investorgain.com/cloud/v2/report/data-read/331/1/{month}/{year}/0/0/all"

    def __init__(self):
        super().__init__()
        self.api_headers = {
            "User-Agent": SCRAPER_USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.investorgain.com",
            "Referer": "https://www.investorgain.com/",
        }

    def fetch_and_parse(self) -> List[NormalizedIPO]:
        """
        Fetches live unofficial Grey Market Premium (GMP) data directly from
        InvestorGain's cloud/v2 REST service.
        """
        results: List[NormalizedIPO] = []
        now = datetime.now(timezone.utc)
        current_month = now.month
        current_year = now.year

        url = self.API_DATA_URL.format(month=current_month, year=current_year)

        with httpx.Client(headers=self.api_headers, follow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS) as client:
            try:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    rows = data.get("reportTableData", [])
                    results = self._parse_gmp_rows(rows, now)
                    logger.info(f"[{self.name}] Parsed {len(results)} live GMP records")
                else:
                    logger.warning(f"[{self.name}] API returned HTTP {res.status_code} from {url}")
            except Exception as e:
                logger.error(f"[{self.name}] Error fetching InvestorGain data: {e}")

        logger.info(f"[{self.name}] Total parsed items: {len(results)}")
        return results

    def _parse_gmp_rows(self, rows: List[dict], recorded_at: datetime) -> List[NormalizedIPO]:
        ipos: List[NormalizedIPO] = []

        for item in rows:
            try:
                raw_name = item.get("~ipo_name")
                if not raw_name:
                    name_html = item.get("Name", "")
                    if name_html:
                        soup = BeautifulSoup(name_html, "html.parser")
                        raw_name = soup.get_text(strip=True)

                if not raw_name:
                    continue

                clean_name = DataValidator.clean_company_name(raw_name)
                if not clean_name:
                    continue

                category = item.get("~IPO_Category") or item.get("~ipo_category1") or ""
                ipo_type = "SME" if "sme" in category.lower() or "sme" in clean_name.lower() else "Mainboard"
                slug = self.generate_slug(clean_name, ipo_type)

                detail_url_path = item.get("~urlrewrite_folder_name", "")
                detail_url = f"{self.base_url}{detail_url_path}" if detail_url_path else self.base_url

                # Dates
                open_date = DataValidator.parse_indian_date(item.get("~Srt_Open") or item.get("Open"))
                close_date = DataValidator.parse_indian_date(item.get("~Srt_Close") or item.get("Close"))
                allotment_date = DataValidator.parse_indian_date(item.get("~Srt_BoA_Dt") or item.get("BoA Dt"))
                listing_date = DataValidator.parse_indian_date(item.get("~Str_Listing") or item.get("Listing"))

                # Pricing & lot
                price_val = self._parse_float(item.get("Price (₹)"))
                lot_str = str(item.get("Lot", "")).strip()
                lot_val = int(lot_str) if lot_str.isdigit() else None
                issue_size = self._parse_float(item.get("IPO Size"))

                min_inv = None
                if lot_val and price_val:
                    min_inv = round(lot_val * price_val, 2)

                # Parse GMP
                gmp_obj = None
                raw_gmp = item.get("~max_gmp1")
                if raw_gmp is not None:
                    try:
                        gmp_val = float(raw_gmp)
                        gain_pct = self._parse_float(item.get("~gmp_percent_calc"))
                        est_price = round(price_val + gmp_val, 2) if price_val else None

                        # Strip fire rating emojis
                        rating_html = item.get("Rating", "")
                        rating_val = None
                        if rating_html:
                            soup = BeautifulSoup(rating_html, "html.parser")
                            rating_val = soup.get_text(strip=True)

                        gmp_obj = NormalizedGMP(
                            gmp=gmp_val,
                            estimated_listing_price=est_price,
                            estimated_gain_percent=gain_pct,
                            rating=rating_val,
                            source_name=self.name,
                            source_url=detail_url,
                            recorded_at=recorded_at,
                            raw_data=item
                        )
                    except ValueError:
                        pass

                ipo = NormalizedIPO(
                    company_name=clean_name,
                    slug=slug,
                    ipo_type=ipo_type,
                    status="Upcoming",
                    open_date=open_date,
                    close_date=close_date,
                    allotment_date=allotment_date,
                    listing_date=listing_date,
                    price_band_low=price_val,
                    price_band_high=price_val,
                    lot_size=lot_val,
                    minimum_investment=min_inv,
                    issue_size=issue_size,
                    source_name=self.name,
                    source_url=detail_url,
                    source_id=str(item.get("~id", slug)),
                    current_gmp=gmp_obj,
                    raw_data=item
                )
                ipos.append(ipo)

            except Exception as e:
                logger.error(f"[{self.name}] Error parsing GMP row: {e}")
                continue

        return ipos

    @staticmethod
    def _parse_float(val: Optional[str]) -> Optional[float]:
        if val is None:
            return None
        cleaned = re.sub(r'[^\d\.\-]', '', str(val)).strip()
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
