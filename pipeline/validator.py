import re
import logging
from typing import Optional, Tuple
from datetime import datetime, date
from pipeline.models import NormalizedIPO, NormalizedGMP

logger = logging.getLogger("ipodecoded.validator")

class DataValidator:
    @staticmethod
    def clean_company_name(name: str) -> str:
        if not name:
            return ""
        cleaned = name.strip()
        # Remove (SME) or [SME] tags
        cleaned = re.sub(r'[\(\[]\s*SME\s*[\)\]]', '', cleaned, flags=re.IGNORECASE)
        # Remove trailing IPO / IPO GMP / SME IPO
        cleaned = re.sub(r'\s+(?:-|–)?\s*(?:SME\s+)?IPO(?:\s+GMP)?\b', '', cleaned, flags=re.IGNORECASE)
        # Remove corporate designators at the end
        cleaned = re.sub(r'\s+(?:Private\s+Limited|Pvt\.?\s*Ltd\.?|Ltd\.?|Limited)\b', '', cleaned, flags=re.IGNORECASE)
        # Remove trailing IPO again if it was 'Ltd IPO'
        cleaned = re.sub(r'\s+(?:-|–)?\s*(?:SME\s+)?IPO(?:\s+GMP)?\b', '', cleaned, flags=re.IGNORECASE)
        # Normalize whitespace and strip trailing punctuation
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(" .,-")
        return cleaned

    @staticmethod
    def parse_indian_date(date_str: Optional[str]) -> Optional[date]:
        """
        Parses various Indian date formats commonly found in financial tables:
        e.g., '10 Sep 2026', '10-09-2026', 'Sep 10, 2026', '10-Sep-2026', '2026-09-10'
        """
        if not date_str or date_str.strip().lower() in ["-", "n/a", "na", "tba", "--", "null", "none"]:
            return None

        clean_str = date_str.strip()
        # Remove ordinal suffixes like 1st, 2nd, 3rd, 4th
        clean_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', clean_str)

        formats = [
            "%d %b %Y",    # 10 Sep 2026
            "%d %B %Y",    # 10 September 2026
            "%d-%b-%Y",    # 10-Sep-2026
            "%d-%m-%Y",    # 10-09-2026
            "%Y-%m-%d",    # 2026-09-10
            "%b %d, %Y",   # Sep 10, 2026
            "%d/%m/%Y",    # 10/09/2026
            "%d-%b-%y",    # 10-Sep-26
        ]

        for fmt in formats:
            try:
                return datetime.strptime(clean_str, fmt).date()
            except ValueError:
                continue

        # Try extract DD MMM YYYY via regex
        match = re.search(r'(\d{1,2})[\s\-]+([A-Za-z]{3,9})[\s\-]+(\d{4})', clean_str)
        if match:
            day, month, year = match.groups()
            for m_fmt in ["%b", "%B"]:
                try:
                    dt = datetime.strptime(f"{day} {month} {year}", f"%d {m_fmt} %Y")
                    return dt.date()
                except ValueError:
                    pass

        logger.warning(f"Unable to parse date string: '{date_str}'")
        return None

    @staticmethod
    def parse_price_band(price_str: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
        """
        Parses price band formats:
        'Rs.601 to Rs.632', '₹450 to ₹475', '450 - 475', '₹100', '100', etc.
        """
        if not price_str:
            return None, None

        # Clean currency prefixes and commas
        cleaned = re.sub(r'(?:Rs\.?|INR|₹)', '', price_str, flags=re.IGNORECASE).replace(',', '').strip()
        # Look for range: e.g. 450 to 475 or 450 - 475
        range_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)', cleaned, flags=re.IGNORECASE)
        if range_match:
            try:
                low = float(range_match.group(1))
                high = float(range_match.group(2))
                if low > high:
                    low, high = high, low
                return low, high
            except ValueError:
                pass

        # Look for single price
        single_match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
        if single_match:
            try:
                val = float(single_match.group(1))
                return val, val
            except ValueError:
                pass

        return None, None

    @classmethod
    def validate_ipo(cls, ipo: NormalizedIPO) -> bool:
        """
        Validates an IPO instance before persisting.
        Returns True if valid, False if rejected.
        """
        if not ipo.company_name or not ipo.company_name.strip():
            logger.error("Rejected IPO: Empty company name")
            return False

        if ipo.price_band_low is not None and ipo.price_band_high is not None:
            if ipo.price_band_low < 0 or ipo.price_band_high < 0:
                logger.error(f"Rejected IPO {ipo.company_name}: Negative price in band")
                return False
            if ipo.price_band_low > ipo.price_band_high:
                # Auto correct if inverted
                ipo.price_band_low, ipo.price_band_high = ipo.price_band_high, ipo.price_band_low

        if ipo.lot_size is not None and ipo.lot_size <= 0:
            logger.warning(f"Invalid lot size {ipo.lot_size} for {ipo.company_name}. Setting to None.")
            ipo.lot_size = None

        # Calculate minimum_investment if lot_size and price_band_high are present
        if ipo.lot_size and ipo.price_band_high and not ipo.minimum_investment:
            ipo.minimum_investment = round(ipo.lot_size * ipo.price_band_high, 2)

        # Ensure status is valid
        valid_statuses = ["Upcoming", "Open", "Closed", "Listed"]
        if ipo.status not in valid_statuses:
            ipo.status = "Upcoming"

        return True

    @classmethod
    def validate_gmp(cls, gmp: NormalizedGMP, price_band_high: Optional[float] = None) -> bool:
        """
        Validates GMP record.
        GMP can be positive, 0, or negative (discount).
        """
        if gmp.gmp is None:
            return False

        # Calculate estimated listing price & gain if price_band_high available
        if price_band_high and price_band_high > 0:
            if gmp.estimated_listing_price is None:
                gmp.estimated_listing_price = round(price_band_high + gmp.gmp, 2)
            if gmp.estimated_gain_percent is None:
                gmp.estimated_gain_percent = round((gmp.gmp / price_band_high) * 100, 2)

        return True
