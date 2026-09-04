from typing import Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field

class NormalizedGMP(BaseModel):
    gmp: float
    estimated_listing_price: Optional[float] = None
    estimated_gain_percent: Optional[float] = None
    kostak: Optional[float] = None
    subject_to_sauda: Optional[float] = None
    rating: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Optional[Dict[str, Any]] = None

class NormalizedIPO(BaseModel):
    company_name: str
    slug: str
    ipo_type: str = "Mainboard"  # 'Mainboard' or 'SME'
    status: str = "Upcoming"     # 'Upcoming', 'Open', 'Closed', 'Listed'
    
    # Dates
    open_date: Optional[date] = None
    close_date: Optional[date] = None
    allotment_date: Optional[date] = None
    refund_date: Optional[date] = None
    demat_date: Optional[date] = None
    listing_date: Optional[date] = None

    # Pricing & Lot size
    price_band_low: Optional[float] = None
    price_band_high: Optional[float] = None
    lot_size: Optional[int] = None
    minimum_investment: Optional[float] = None

    # Issue metrics
    issue_size: Optional[float] = None      # In Crores
    fresh_issue: Optional[float] = None     # In Crores
    ofs: Optional[float] = None             # In Crores
    face_value: Optional[float] = None
    shares_offered: Optional[int] = None
    shares_bid: Optional[int] = None

    # Subscription data
    subscription_status: Optional[str] = None
    subscription_retail: Optional[float] = None
    subscription_qib: Optional[float] = None
    subscription_nii: Optional[float] = None
    subscription_total: Optional[float] = None

    # Description & Source
    symbol: Optional[str] = None
    company_description: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_id: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    # Associated GMP if parsed together
    current_gmp: Optional[NormalizedGMP] = None

