import json
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Numeric, 
    Date, DateTime, Text, Boolean, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.config import DATABASE_URL

# Handle SQLite vs Postgres connection args
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class IPO(Base):
    __tablename__ = "ipos"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    ipo_type = Column(String(20), nullable=False, default="Mainboard", index=True)  # 'Mainboard', 'SME'
    status = Column(String(20), nullable=False, default="Upcoming", index=True)      # 'Upcoming', 'Open', 'Closed', 'Listed'

    # Timeline dates
    open_date = Column(Date, nullable=True)
    close_date = Column(Date, nullable=True)
    allotment_date = Column(Date, nullable=True)
    refund_date = Column(Date, nullable=True)
    demat_date = Column(Date, nullable=True)
    listing_date = Column(Date, nullable=True)

    # Pricing and lot metrics
    price_band_low = Column(Numeric(12, 2), nullable=True)
    price_band_high = Column(Numeric(12, 2), nullable=True)
    lot_size = Column(Integer, nullable=True)
    minimum_investment = Column(Numeric(12, 2), nullable=True)

    # Issue metrics (in Crores INR)
    issue_size = Column(Numeric(14, 2), nullable=True)
    fresh_issue = Column(Numeric(14, 2), nullable=True)
    ofs = Column(Numeric(14, 2), nullable=True)
    face_value = Column(Numeric(10, 2), nullable=True)

    # Subscription data
    subscription_status = Column(String(50), nullable=True)
    subscription_retail = Column(Numeric(8, 2), nullable=True)
    subscription_qib = Column(Numeric(8, 2), nullable=True)
    subscription_nii = Column(Numeric(8, 2), nullable=True)
    subscription_total = Column(Numeric(8, 2), nullable=True)

    # Context & source audit
    company_description = Column(Text, nullable=True)
    source_name = Column(String(100), nullable=True)
    source_url = Column(Text, nullable=True)
    source_id = Column(String(100), nullable=True)

    # Cross-source verification & validation semantics
    master_data_validated = Column(Boolean, default=False, nullable=False)
    gmp_sources_available = Column(Boolean, default=False, nullable=False)
    gmp_divergence_alert = Column(Boolean, default=False, nullable=False)
    is_cross_validated = Column(Boolean, default=False, nullable=False)
    has_conflicts = Column(Boolean, default=False, nullable=False)
    conflicts_json = Column(Text, nullable=True)
    sources_verified = Column(Text, nullable=True)  # JSON array of source names e.g. ["NSE", "Chittorgarh"]

    # Explicit Dual-GMP and Spread metrics
    gmp_investorgain = Column(Numeric(10, 2), nullable=True)  # Primary GMP: InvestorGain
    gmp_ipowatch = Column(Numeric(10, 2), nullable=True)      # Secondary GMP: IPOWatch
    current_gmp_secondary = Column(Numeric(10, 2), nullable=True)  # Backwards-compatible alias for gmp_ipowatch
    gmp_spread = Column(String(50), nullable=True)
    gmp_spread_low = Column(Numeric(10, 2), nullable=True)
    gmp_spread_high = Column(Numeric(10, 2), nullable=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    gmp_records = relationship("IPOGMP", back_populates="ipo", cascade="all, delete-orphan", order_by="desc(IPOGMP.recorded_at)")
    sources = relationship("IPOSource", back_populates="ipo", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ipos_open_close", "open_date", "close_date"),
    )

    def to_dict(self, include_latest_gmp=True):
        # Precise source GMPs
        ig_gmp = float(self.gmp_investorgain) if self.gmp_investorgain is not None else None
        iw_gmp = float(self.gmp_ipowatch) if self.gmp_ipowatch is not None else (
            float(self.current_gmp_secondary) if self.current_gmp_secondary is not None else None
        )

        # Primary GMP preference: InvestorGain (primary), fallback to IPOWatch if IG missing
        current_gmp = ig_gmp if ig_gmp is not None else iw_gmp
        gmp_source_name = "InvestorGain" if ig_gmp is not None else ("IPOWatch" if iw_gmp is not None else None)
        gmp_updated_at = None

        if current_gmp is None and self.gmp_records:
            latest_gmp_record = self.gmp_records[0]
            current_gmp = float(latest_gmp_record.gmp)
            gmp_source_name = latest_gmp_record.source_name
            gmp_updated_at = latest_gmp_record.recorded_at.isoformat() if latest_gmp_record.recorded_at else None

        # Calculate derived estimates if price band available
        est_price = None
        est_gain_pct = None
        if current_gmp is not None and self.price_band_high:
            pb_high = float(self.price_band_high)
            est_price = round(pb_high + current_gmp, 2)
            if pb_high > 0:
                est_gain_pct = round((current_gmp / pb_high) * 100, 2)

        # Spread metrics
        spread_low = float(self.gmp_spread_low) if self.gmp_spread_low is not None else (
            min(ig_gmp, iw_gmp) if ig_gmp is not None and iw_gmp is not None else current_gmp
        )
        spread_high = float(self.gmp_spread_high) if self.gmp_spread_high is not None else (
            max(ig_gmp, iw_gmp) if ig_gmp is not None and iw_gmp is not None else current_gmp
        )
        gmp_spread_str = self.gmp_spread
        if not gmp_spread_str and spread_low is not None and spread_high is not None:
            gmp_spread_str = f"₹{spread_low:.0f} – ₹{spread_high:.0f}" if spread_low != spread_high else f"₹{spread_low:.0f}"

        # Parse sources_verified
        sources_list = []
        if self.sources_verified:
            try:
                sources_list = json.loads(self.sources_verified) if isinstance(self.sources_verified, str) else self.sources_verified
            except Exception:
                sources_list = [self.sources_verified]

        # Parse conflicts
        conflicts_dict = None
        if self.conflicts_json:
            try:
                conflicts_dict = json.loads(self.conflicts_json)
            except Exception:
                conflicts_dict = None

        return {
            "id": self.id,
            "company_name": self.company_name,
            "slug": self.slug,
            "ipo_type": self.ipo_type,
            "status": self.status,
            "open_date": self.open_date.isoformat() if self.open_date else None,
            "close_date": self.close_date.isoformat() if self.close_date else None,
            "allotment_date": self.allotment_date.isoformat() if self.allotment_date else None,
            "refund_date": self.refund_date.isoformat() if self.refund_date else None,
            "demat_date": self.demat_date.isoformat() if self.demat_date else None,
            "listing_date": self.listing_date.isoformat() if self.listing_date else None,
            "price_band_low": float(self.price_band_low) if self.price_band_low is not None else None,
            "price_band_high": float(self.price_band_high) if self.price_band_high is not None else None,
            "lot_size": self.lot_size,
            "minimum_investment": float(self.minimum_investment) if self.minimum_investment is not None else None,
            "issue_size": float(self.issue_size) if self.issue_size is not None else None,
            "fresh_issue": float(self.fresh_issue) if self.fresh_issue is not None else None,
            "ofs": float(self.ofs) if self.ofs is not None else None,
            "face_value": float(self.face_value) if self.face_value is not None else None,
            "subscription_status": self.subscription_status,
            "subscription_retail": float(self.subscription_retail) if self.subscription_retail is not None else None,
            "subscription_qib": float(self.subscription_qib) if self.subscription_qib is not None else None,
            "subscription_nii": float(self.subscription_nii) if self.subscription_nii is not None else None,
            "subscription_total": float(self.subscription_total) if self.subscription_total is not None else None,
            "company_description": self.company_description,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # Dual GMP & Spread breakdown
            "current_gmp": current_gmp,
            "gmp_investorgain": ig_gmp,
            "gmp_ipowatch": iw_gmp,
            "current_gmp_secondary": iw_gmp,
            "gmp_spread": gmp_spread_str,
            "gmp_spread_low": spread_low,
            "gmp_spread_high": spread_high,
            "estimated_listing_price": est_price,
            "estimated_gain_percent": est_gain_pct,
            "gmp_updated_at": gmp_updated_at,
            "gmp_source_name": gmp_source_name,
            # Validation and Verification Semantics
            "master_data_validated": self.master_data_validated,
            "gmp_sources_available": self.gmp_sources_available,
            "gmp_divergence_alert": self.gmp_divergence_alert,
            "is_cross_validated": self.is_cross_validated,
            "has_conflicts": self.has_conflicts,
            "conflicts": conflicts_dict,
            "sources_verified": sources_list
        }


class IPOSource(Base):
    __tablename__ = "ipo_sources"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ipo_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("ipos.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String(100), nullable=False)  # 'NSE', 'Chittorgarh', 'InvestorGain', 'IPOWatch'
    source_url = Column(Text, nullable=True)
    source_ipo_id = Column(String(100), nullable=True)  # Symbol, ID, or slug on source
    raw_data = Column(Text, nullable=True)  # JSON representation of raw extracted fields
    fetched_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    ipo = relationship("IPO", back_populates="sources")

    def to_dict(self):
        return {
            "id": self.id,
            "ipo_id": self.ipo_id,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "source_ipo_id": self.source_ipo_id,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None
        }


class IPOGMP(Base):
    __tablename__ = "ipo_gmp"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ipo_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("ipos.id", ondelete="CASCADE"), nullable=False, index=True)
    gmp = Column(Numeric(10, 2), nullable=False)
    estimated_listing_price = Column(Numeric(12, 2), nullable=True)
    estimated_gain_percent = Column(Numeric(6, 2), nullable=True)
    kostak = Column(Numeric(10, 2), nullable=True)
    subject_to_sauda = Column(Numeric(10, 2), nullable=True)
    source_name = Column(String(100), nullable=False)  # 'InvestorGain', 'IPOWatch'
    source_url = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    ipo = relationship("IPO", back_populates="gmp_records")

    def to_dict(self):
        return {
            "id": self.id,
            "ipo_id": self.ipo_id,
            "gmp": float(self.gmp),
            "estimated_listing_price": float(self.estimated_listing_price) if self.estimated_listing_price is not None else None,
            "estimated_gain_percent": float(self.estimated_gain_percent) if self.estimated_gain_percent is not None else None,
            "kostak": float(self.kostak) if self.kostak is not None else None,
            "subject_to_sauda": float(self.subject_to_sauda) if self.subject_to_sauda is not None else None,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SourceHealth(Base):
    __tablename__ = "source_health"

    source_id = Column(String(50), primary_key=True)  # 'nse', 'chittorgarh', 'investorgain', 'ipowatch'
    source_name = Column(String(100), nullable=False)
    status = Column(String(20), default="UNKNOWN", nullable=False)  # 'HEALTHY', 'DEGRADED', 'FAILED'
    last_successful_fetch = Column(DateTime(timezone=True), nullable=True)
    last_failed_fetch = Column(DateTime(timezone=True), nullable=True)
    records_returned = Column(Integer, default=0, nullable=False)
    last_error_message = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    def to_dict(self):
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "status": self.status,
            "last_successful_fetch": self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
            "last_failed_fetch": self.last_failed_fetch.isoformat() if self.last_failed_fetch else None,
            "records_returned": self.records_returned,
            "last_error_message": self.last_error_message,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    started_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="RUNNING", nullable=False)  # 'SUCCESS', 'DEGRADED', 'FAILED'
    new_ipos_count = Column(Integer, default=0, nullable=False)
    updated_ipos_count = Column(Integer, default=0, nullable=False)
    gmp_records_count = Column(Integer, default=0, nullable=False)
    conflicts_count = Column(Integer, default=0, nullable=False)
    conflicts_summary = Column(Text, nullable=True)  # JSON string
    sources_summary = Column(Text, nullable=True)    # JSON string
    error_message = Column(Text, nullable=True)

    def to_dict(self):
        conflicts = None
        if self.conflicts_summary:
            try:
                conflicts = json.loads(self.conflicts_summary)
            except Exception:
                conflicts = self.conflicts_summary
        sources = None
        if self.sources_summary:
            try:
                sources = json.loads(self.sources_summary)
            except Exception:
                sources = self.sources_summary

        return {
            "id": self.id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "new_ipos_count": self.new_ipos_count,
            "updated_ipos_count": self.updated_ipos_count,
            "gmp_records_count": self.gmp_records_count,
            "conflicts_count": self.conflicts_count,
            "conflicts_summary": conflicts,
            "sources_summary": sources,
            "error_message": self.error_message
        }


def init_db():
    Base.metadata.create_all(bind=engine)
    # Ensure any new columns added to existing tables in SQLite are added safely if table already existed
    if str(engine.url).startswith("sqlite"):
        import sqlite3
        con = sqlite3.connect(engine.url.database)
        cur = con.cursor()
        existing_cols = [r[1] for r in cur.execute("PRAGMA table_info(ipos)").fetchall()]
        new_cols = [
            ("is_cross_validated", "INTEGER DEFAULT 0"),
            ("has_conflicts", "INTEGER DEFAULT 0"),
            ("conflicts_json", "TEXT"),
            ("sources_verified", "TEXT"),
            ("current_gmp_secondary", "NUMERIC(10,2)"),
            ("gmp_spread", "VARCHAR(50)"),
            ("gmp_investorgain", "NUMERIC(10,2)"),
            ("gmp_ipowatch", "NUMERIC(10,2)"),
            ("gmp_spread_low", "NUMERIC(10,2)"),
            ("gmp_spread_high", "NUMERIC(10,2)"),
            ("master_data_validated", "INTEGER DEFAULT 0"),
            ("gmp_sources_available", "INTEGER DEFAULT 0"),
            ("gmp_divergence_alert", "INTEGER DEFAULT 0")
        ]
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                try:
                    cur.execute(f"ALTER TABLE ipos ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass
        con.commit()
        con.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
