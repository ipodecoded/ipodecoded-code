import logging
import httpx
from abc import ABC, abstractmethod
from typing import List, Optional
from slugify import slugify
from backend.config import SCRAPER_USER_AGENT, REQUEST_TIMEOUT_SECONDS
from pipeline.models import NormalizedIPO

logger = logging.getLogger("ipodecoded.sources.base")

class BaseSourceAdapter(ABC):
    name: str = "BaseSource"
    base_url: str = ""

    def __init__(self):
        self.headers = {
            "User-Agent": SCRAPER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": self.base_url or "https://www.google.com/",
            "Cache-Control": "no-cache",
        }

    def fetch_url(self, url: str) -> Optional[str]:
        """
        Safely fetches content with timeout, headers, and error logging.
        Never crashes the pipeline if a source is down.
        """
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
                response = client.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"[{self.name}] Received HTTP status {response.status_code} from {url}")
                    return None
        except httpx.RequestError as exc:
            logger.error(f"[{self.name}] Network error connecting to {url}: {exc}")
            return None
        except Exception as exc:
            logger.error(f"[{self.name}] Unexpected error fetching {url}: {exc}")
            return None

    @abstractmethod
    def fetch_and_parse(self) -> List[NormalizedIPO]:
        """
        Fetches and parses IPOs into normalized data models.
        """
        pass

    @staticmethod
    def generate_slug(company_name: str, ipo_type: str = "Mainboard") -> str:
        """
        Generates standard URL-safe slugs, e.g. 'bajaj-housing-finance-ipo'
        """
        base = slugify(company_name.strip())
        if not base.endswith("-ipo"):
            base = f"{base}-ipo"
        if ipo_type == "SME" and not "-sme-" in base:
            base = f"{base}-sme"
        return base
