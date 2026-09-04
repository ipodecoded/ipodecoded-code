import logging
import httpx
from typing import List
from pipeline.sources.base import BaseSourceAdapter
from pipeline.models import NormalizedIPO
from pipeline.validator import DataValidator
from backend.config import SCRAPER_USER_AGENT, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger("ipodecoded.sources.nse")

class NSEAdapter(BaseSourceAdapter):
    name: str = "NSE"
    base_url: str = "https://www.nseindia.com"

    CURRENT_ISSUES_URL = "https://www.nseindia.com/api/ipo-current-issue"
    UPCOMING_ISSUES_URL = "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"

    def __init__(self):
        super().__init__()
        self.api_headers = {
            "User-Agent": SCRAPER_USER_AGENT,
            "Accept": "*/*",
            "Referer": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_and_parse(self) -> List[NormalizedIPO]:
        """
        Fetches official primary market IPO data directly from NSE's public APIs.
        Covers active open issues and forthcoming/upcoming issues.
        """
        results: List[NormalizedIPO] = []

        with httpx.Client(headers=self.api_headers, follow_redirects=True, timeout=REQUEST_TIMEOUT_SECONDS) as client:
            # 1. Fetch Current Open Issues
            try:
                r_curr = client.get(self.CURRENT_ISSUES_URL)
                if r_curr.status_code == 200:
                    curr_items = r_curr.json()
                    if isinstance(curr_items, list):
                        for item in curr_items:
                            parsed = self._parse_current_issue(item)
                            if parsed:
                                results.append(parsed)
                        logger.info(f"[{self.name}] Parsed {len(results)} active open issues")
                else:
                    logger.warning(f"[{self.name}] Received HTTP {r_curr.status_code} from {self.CURRENT_ISSUES_URL}")
            except Exception as e:
                logger.error(f"[{self.name}] Error fetching current issues: {e}")

            # 2. Fetch Upcoming / Forthcoming Issues
            try:
                r_up = client.get(self.UPCOMING_ISSUES_URL)
                if r_up.status_code == 200:
                    up_items = r_up.json()
                    if isinstance(up_items, list):
                        up_count = 0
                        for item in up_items:
                            parsed = self._parse_upcoming_issue(item)
                            if parsed:
                                results.append(parsed)
                                up_count += 1
                        logger.info(f"[{self.name}] Parsed {up_count} upcoming forthcoming issues")
                else:
                    logger.warning(f"[{self.name}] Received HTTP {r_up.status_code} from {self.UPCOMING_ISSUES_URL}")
            except Exception as e:
                logger.error(f"[{self.name}] Error fetching upcoming issues: {e}")

        logger.info(f"[{self.name}] Total parsed items: {len(results)}")
        return results

    def _parse_current_issue(self, item: dict) -> NormalizedIPO:
        company_name = item.get("companyName", "").strip()
        if not company_name:
            return None

        clean_name = DataValidator.clean_company_name(company_name)
        series = item.get("series", "").upper()
        ipo_type = "SME" if "SME" in series or "SME" in clean_name.upper() else "Mainboard"
        slug = self.generate_slug(clean_name, ipo_type)

        open_date = DataValidator.parse_indian_date(item.get("issueStartDate"))
        close_date = DataValidator.parse_indian_date(item.get("issueEndDate"))

        # Live subscription bidding multiple
        sub_total = None
        no_of_time = item.get("noOfTime")
        if no_of_time:
            try:
                sub_total = float(no_of_time)
            except ValueError:
                pass

        sub_status = f"Subscribed {sub_total}x" if sub_total is not None else "Open for Bidding"

        shares_bid = None
        if item.get("noOfsharesBid") and str(item.get("noOfsharesBid")).isdigit():
            shares_bid = int(item.get("noOfsharesBid"))

        shares_offered = None
        if item.get("noOfSharesOffered") and str(item.get("noOfSharesOffered")).isdigit():
            shares_offered = int(item.get("noOfSharesOffered"))

        return NormalizedIPO(
            company_name=clean_name,
            slug=slug,
            ipo_type=ipo_type,
            status="Open",
            open_date=open_date,
            close_date=close_date,
            subscription_status=sub_status,
            subscription_total=sub_total,
            shares_bid=shares_bid,
            shares_offered=shares_offered,
            symbol=item.get("symbol"),
            source_name=self.name,
            source_url=self.CURRENT_ISSUES_URL,
            source_id=item.get("symbol"),
            raw_data=item
        )

    def _parse_upcoming_issue(self, item: dict) -> NormalizedIPO:
        company_name = item.get("companyName", "").strip()
        if not company_name:
            return None

        clean_name = DataValidator.clean_company_name(company_name)
        series = item.get("series", "").upper()
        ipo_type = "SME" if "SME" in series or "SME" in clean_name.upper() else "Mainboard"
        slug = self.generate_slug(clean_name, ipo_type)

        open_date = DataValidator.parse_indian_date(item.get("issueStartDate"))
        close_date = DataValidator.parse_indian_date(item.get("issueEndDate"))

        # Parse price band (e.g. "Rs.601 to Rs.632")
        price_str = item.get("issuePrice")
        pb_low, pb_high = DataValidator.parse_price_band(price_str)

        shares_offered = None
        if item.get("issueSize") and str(item.get("issueSize")).isdigit():
            shares_offered = int(item.get("issueSize"))

        # Compute issue size in Crores if shares_offered and price are available
        issue_size_cr = None
        if shares_offered and pb_high:
            issue_size_cr = round((shares_offered * pb_high) / 10000000.0, 2)

        return NormalizedIPO(
            company_name=clean_name,
            slug=slug,
            ipo_type=ipo_type,
            status="Upcoming",
            open_date=open_date,
            close_date=close_date,
            price_band_low=pb_low,
            price_band_high=pb_high,
            shares_offered=shares_offered,
            issue_size=issue_size_cr,
            subscription_status="Not Yet Open",
            symbol=item.get("symbol"),
            source_name=self.name,
            source_url=self.UPCOMING_ISSUES_URL,
            source_id=item.get("symbol"),
            raw_data=item
        )
