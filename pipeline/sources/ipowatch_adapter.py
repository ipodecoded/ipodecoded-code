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

logger = logging.getLogger("ipodecoded.sources.ipowatch")

class IPOWatchAdapter(BaseSourceAdapter):
    name: str = "IPOWatch"
    base_url: str = "https://ipowatch.in"
    GMP_URL = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"

    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": SCRAPER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://www.google.com/",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_and_parse(self) -> List[NormalizedIPO]:
        """
        Fetches independent secondary GMP market quotes from IPOWatch's live HTML tables.
        Parses Table 0 (Mainboard) and Table 1 (SME).
        """
        results: List[NormalizedIPO] = []
        now = datetime.now(timezone.utc)

        try:
            with httpx.Client(headers=self.headers, follow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS) as client:
                res = client.get(self.GMP_URL)
                if res.status_code != 200:
                    logger.warning(f"[{self.name}] Received HTTP status {res.status_code} from {self.GMP_URL}")
                    return []
                html = res.text
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching {self.GMP_URL}: {e}")
            return []

        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")

        if not tables:
            logger.warning(f"[{self.name}] No tables found on GMP page")
            return []

        # Table 0: Mainboard IPO GMP
        if len(tables) >= 1:
            mb_ipos = self._parse_table(tables[0], ipo_type="Mainboard", recorded_at=now)
            results.extend(mb_ipos)
            logger.info(f"[{self.name}] Parsed {len(mb_ipos)} Mainboard GMP records")

        # Table 1: SME IPO GMP
        if len(tables) >= 2:
            sme_ipos = self._parse_table(tables[1], ipo_type="SME", recorded_at=now)
            results.extend(sme_ipos)
            logger.info(f"[{self.name}] Parsed {len(sme_ipos)} SME GMP records")

        logger.info(f"[{self.name}] Total parsed items: {len(results)}")
        return results

    def _parse_table(self, table, ipo_type: str, recorded_at: datetime) -> List[NormalizedIPO]:
        ipos: List[NormalizedIPO] = []
        rows = table.find_all("tr")
        if len(rows) < 2:
            return []

        # First row is headers
        header_cols = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]

        for row in rows[1:]:
            cols = row.find_all(["td", "th"])
            if len(cols) < 4:
                continue

            try:
                raw_name = cols[0].get_text(strip=True)
                # Remove suffixes like ' IPO'
                raw_name = re.sub(r'\s*IPO.*$', '', raw_name, flags=re.IGNORECASE)
                clean_name = DataValidator.clean_company_name(raw_name)
                if not clean_name:
                    continue

                slug = self.generate_slug(clean_name, ipo_type)

                # Col 1 is GMP: e.g. "₹18", "₹0", "₹55"
                gmp_text = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                gmp_val = self._parse_float(gmp_text)

                # Trend emoji / badge
                trend_val = cols[2].get_text(strip=True) if len(cols) > 2 else ""

                # Price band
                price_text = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                pb_low, pb_high = DataValidator.parse_price_band(price_text)

                # Estimated listing / gain
                est_listing_text = cols[4].get_text(strip=True) if len(cols) > 4 else ""
                est_price = None
                gain_pct = None
                est_match = re.search(r'([\d\.]+)\s*\(([\d\.\-]+)%\)', est_listing_text)
                if est_match:
                    est_price = float(est_match.group(1))
                    gain_pct = float(est_match.group(2))
                elif pb_high and gmp_val is not None:
                    est_price = round(pb_high + gmp_val, 2)
                    gain_pct = round((gmp_val / pb_high) * 100, 2) if pb_high > 0 else 0.0

                # Status
                status_text = cols[6].get_text(strip=True) if len(cols) > 6 else "Upcoming"
                status = "Upcoming"
                if "open" in status_text.lower():
                    status = "Open"
                elif "closed" in status_text.lower():
                    status = "Closed"
                elif "listed" in status_text.lower():
                    status = "Listed"

                gmp_obj = None
                if gmp_val is not None:
                    gmp_obj = NormalizedGMP(
                        gmp=gmp_val,
                        estimated_listing_price=est_price,
                        estimated_gain_percent=gain_pct,
                        rating=trend_val,
                        source_name=self.name,
                        source_url=self.GMP_URL,
                        recorded_at=recorded_at,
                        raw_data={
                            "company": clean_name,
                            "gmp_raw": gmp_text,
                            "price_raw": price_text,
                            "est_raw": est_listing_text,
                            "status": status_text
                        }
                    )

                ipo = NormalizedIPO(
                    company_name=clean_name,
                    slug=slug,
                    ipo_type=ipo_type,
                    status=status,
                    price_band_low=pb_low,
                    price_band_high=pb_high,
                    source_name=self.name,
                    source_url=self.GMP_URL,
                    source_id=slug,
                    current_gmp=gmp_obj,
                    raw_data={"row_text": [c.get_text(strip=True) for c in cols]}
                )
                ipos.append(ipo)

            except Exception as e:
                logger.error(f"[{self.name}] Error parsing row: {e}")
                continue

        return ipos

    @staticmethod
    def _parse_float(val: Optional[str]) -> Optional[float]:
        if not val:
            return None
        cleaned = re.sub(r'[^\d\.\-]', '', str(val)).strip()
        if not cleaned or cleaned == "-":
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
