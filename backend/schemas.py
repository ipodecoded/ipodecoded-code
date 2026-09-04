from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import date, datetime

class GMPRecordSchema(BaseModel):
    id: int
    ipo_id: int
    gmp: float
    estimated_listing_price: Optional[float] = None
    estimated_gain_percent: Optional[float] = None
    kostak: Optional[float] = None
    subject_to_sauda: Optional[float] = None
    source_name: str
    source_url: Optional[str] = None
    recorded_at: Optional[str] = None
    created_at: Optional[str] = None

class IPOSummarySchema(BaseModel):
    id: int
    company_name: str
    slug: str
    ipo_type: str
    status: str
    open_date: Optional[str] = None
    close_date: Optional[str] = None
    allotment_date: Optional[str] = None
    refund_date: Optional[str] = None
    demat_date: Optional[str] = None
    listing_date: Optional[str] = None
    price_band_low: Optional[float] = None
    price_band_high: Optional[float] = None
    lot_size: Optional[int] = None
    minimum_investment: Optional[float] = None
    issue_size: Optional[float] = None
    fresh_issue: Optional[float] = None
    ofs: Optional[float] = None
    face_value: Optional[float] = None
    subscription_status: Optional[str] = None
    subscription_retail: Optional[float] = None
    subscription_qib: Optional[float] = None
    subscription_nii: Optional[float] = None
    subscription_total: Optional[float] = None
    company_description: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    current_gmp: Optional[float] = None
    gmp_investorgain: Optional[float] = None
    gmp_ipowatch: Optional[float] = None
    current_gmp_secondary: Optional[float] = None
    gmp_spread: Optional[str] = None
    gmp_spread_low: Optional[float] = None
    gmp_spread_high: Optional[float] = None
    estimated_listing_price: Optional[float] = None
    estimated_gain_percent: Optional[float] = None
    gmp_updated_at: Optional[str] = None
    gmp_source_name: Optional[str] = None
    master_data_validated: bool = False
    gmp_sources_available: bool = False
    gmp_divergence_alert: bool = False
    is_cross_validated: bool = False
    has_conflicts: bool = False
    conflicts: Optional[Any] = None
    sources_verified: Optional[List[str]] = None

class IPOListResponse(BaseModel):
    total: int
    items: List[IPOSummarySchema]

class StatsResponse(BaseModel):
    total_active_ipos: int
    open_ipos_count: int
    upcoming_ipos_count: int
    recently_closed_count: int
    recently_listed_count: int
    mainboard_count: int
    sme_count: int
    top_gmp_gainers: List[IPOSummarySchema]

class SourceHealthSchema(BaseModel):
    source_id: str
    source_name: str
    status: str
    last_successful_fetch: Optional[str] = None
    last_failed_fetch: Optional[str] = None
    records_returned: int
    last_error_message: Optional[str] = None
    updated_at: Optional[str] = None

class PipelineRunSchema(BaseModel):
    id: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str
    new_ipos_count: int
    updated_ipos_count: int
    gmp_records_count: int
    conflicts_count: int
    conflicts_summary: Optional[Any] = None
    sources_summary: Optional[Any] = None
    error_message: Optional[str] = None

