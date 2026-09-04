import re
import logging
import httpx
from typing import List, Optional
from bs4 import BeautifulSoup
from datetime import date, datetime, timezone
from pipeline.sources.base import BaseSourceAdapter
from pipeline.models import NormalizedIPO
from pipeline.validator import DataValidator
from backend.config import SCRAPER_USER_AGENT, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger("ipodecoded.sources.chittorgarh")

class ChittorgarhAdapter(BaseSourceAdapter):
    name: str = "Chittorgarh"
    base_url: str = "https://www.chittorgarh.com"

    API_DATA_URL = "https://webnodejs.chittorgarh.com/cloud/report/data-read/82/1/{month}/{year}/0/0/{segment}/0?search=&v=18-06"

    def __init__(self):
        super().__init__()
        self.api_headers = {
            "User-Agent": SCRAPER_USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.chittorgarh.com",
            "Referer": "https://www.chittorgarh.com/",
        }

    def fetch_and_parse(self) -> List[NormalizedIPO]:
        """
        Fetches full live IPO master data from Chittorgarh's cloud REST data service.
        Retrieves both Mainboard and SME datasets.
        """
        results: List[NormalizedIPO] = []
        now = datetime.now(timezone.utc)
        current_month = now.month
        current_year = now.year

        with httpx.Client(headers=self.api_headers, follow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS) as client:
            # 1. Fetch Mainboard IPOs
            url_mainboard = self.API_DATA_URL.format(month=current_month, year=current_year, segment="mainboard")
            try:
                r_main = client.get(url_mainboard)
                if r_main.status_code == 200:
                    data = r_main.json()
                    rows = data.get("reportTableData", [])
                    mainboard_ipos = self._parse_rows(rows, ipo_type="Mainboard")
                    results.extend(mainboard_ipos)
                    logger.info(f"[{self.name}] Parsed {len(mainboard_ipos)} live Mainboard IPOs")
                else:
                    logger.warning(f"[{self.name}] Mainboard API returned status {r_main.status_code}")
            except Exception as e:
                logger.error(f"[{self.name}] Error fetching Mainboard data: {e}")

            # 2. Fetch SME IPOs
            url_sme = self.API_DATA_URL.format(month=current_month, year=current_year, segment="sme")
            try:
                r_sme = client.get(url_sme)
                if r_sme.status_code == 200:
                    data = r_sme.json()
                    rows = data.get("reportTableData", [])
                    sme_ipos = self._parse_rows(rows, ipo_type="SME")
                    results.extend(sme_ipos)
                    logger.info(f"[{self.name}] Parsed {len(sme_ipos)} live SME IPOs")
                else:
                    logger.warning(f"[{self.name}] SME API returned status {r_sme.status_code}")
            except Exception as e:
                logger.error(f"[{self.name}] Error fetching SME data: {e}")

        logger.info(f"[{self.name}] Total parsed items: {len(results)}")
        return results

    def _parse_rows(self, rows: List[dict], ipo_type: str) -> List[NormalizedIPO]:
        ipos: List[NormalizedIPO] = []
        today = date.today()

        for item in rows:
            try:
                company_html = item.get("Company", "")
                if not company_html:
                    continue

                # Extract company name and detail url from html anchor
                soup = BeautifulSoup(company_html, "html.parser")
                a_tag = soup.find("a")
                raw_name = a_tag.get_text(strip=True) if a_tag else soup.get_text(strip=True)
                detail_url = a_tag.get("href") if a_tag and a_tag.has_attr("href") else None

                company_name = DataValidator.clean_company_name(raw_name)
                if not company_name:
                    continue

                slug = item.get("~URLRewrite_Folder_Name")
                if not slug or not slug.strip():
                    slug = self.generate_slug(company_name, ipo_type)

                # Parse dates
                open_date = DataValidator.parse_indian_date(item.get("Opening Date"))
                close_date = DataValidator.parse_indian_date(item.get("Closing Date"))
                listing_date = DataValidator.parse_indian_date(item.get("Listing Date"))

                # Parse price band
                price_str = item.get("Issue Price (Rs.)")
                pb_low, pb_high = DataValidator.parse_price_band(price_str)

                # Parse issue size
                issue_size = self._parse_float(item.get("Issue Amount (Rs.cr.)") or item.get("Total Issue Amount (Incl.Firm reservations) (Rs.cr.)"))
                fresh_issue = self._parse_float(item.get("Fresh Capital (Rs.cr.)"))
                ofs = self._parse_float(item.get("Offer for sale (Rs.cr.)"))

                # Status calculation
                status = "Upcoming"
                if listing_date and today >= listing_date:
                    status = "Listed"
                elif close_date and today > close_date:
                    status = "Closed"
                elif open_date and close_date and open_date <= today <= close_date:
                    status = "Open"
                else:
                    status = "Upcoming"

                # Description / Lead Manager
                lead_mgr_html = item.get("Left Lead Manager", "")
                lead_mgr = ""
                if lead_mgr_html:
                    mgr_soup = BeautifulSoup(lead_mgr_html, "html.parser")
                    lead_mgr = mgr_soup.get_text(strip=True)

                desc_parts = []
                if lead_mgr:
                    desc_parts.append(f"Lead Manager: {lead_mgr}")
                if item.get("Listing at"):
                    desc_parts.append(f"Listing: {item.get('Listing at')}")
                if item.get("Pricing Method"):
                    desc_parts.append(f"Method: {item.get('Pricing Method')}")

                company_desc = " • ".join(desc_parts) if desc_parts else None

                ipo = NormalizedIPO(
                    company_name=company_name,
                    slug=slug,
                    ipo_type=ipo_type,
                    status=status,
                    open_date=open_date,
                    close_date=close_date,
                    listing_date=listing_date,
                    price_band_low=pb_low,
                    price_band_high=pb_high,
                    issue_size=issue_size,
                    fresh_issue=fresh_issue,
                    ofs=ofs,
                    company_description=company_desc,
                    source_name=self.name,
                    source_url=detail_url or f"{self.base_url}/ipo/{slug}/",
                    source_id=slug,
                    raw_data=item
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
        cleaned = re.sub(r'[^\d\.]', '', str(val)).strip()
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
