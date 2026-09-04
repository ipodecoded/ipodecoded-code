-- ====================================================================
-- IPODecoded (A JournalDecoded.in Product) - Database Schema
-- Compatible with PostgreSQL 13+ and Supabase Free Tier
-- ====================================================================

-- 1. Create IPOS table
CREATE TABLE IF NOT EXISTS ipos (
    id BIGSERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    ipo_type VARCHAR(20) NOT NULL DEFAULT 'Mainboard', -- 'Mainboard', 'SME'
    status VARCHAR(20) NOT NULL DEFAULT 'Upcoming',     -- 'Upcoming', 'Open', 'Closed', 'Listed'
    
    -- Timeline dates
    open_date DATE,
    close_date DATE,
    allotment_date DATE,
    refund_date DATE,
    demat_date DATE,
    listing_date DATE,
    
    -- Pricing and lots
    price_band_low NUMERIC(12, 2),
    price_band_high NUMERIC(12, 2),
    lot_size INTEGER,
    minimum_investment NUMERIC(12, 2),
    
    -- Issue metrics (in Crores INR)
    issue_size NUMERIC(14, 2),
    fresh_issue NUMERIC(14, 2),
    ofs NUMERIC(14, 2),
    face_value NUMERIC(10, 2),
    
    -- Subscription data
    subscription_status VARCHAR(50),
    subscription_retail NUMERIC(8, 2),
    subscription_qib NUMERIC(8, 2),
    subscription_nii NUMERIC(8, 2),
    subscription_total NUMERIC(8, 2),
    
    -- Company profile & Source tracking
    company_description TEXT,
    source_name VARCHAR(100),
    source_url TEXT,
    source_id VARCHAR(100),
    
    -- Cross-source verification & validation semantics
    master_data_validated BOOLEAN NOT NULL DEFAULT FALSE,
    gmp_sources_available BOOLEAN NOT NULL DEFAULT FALSE,
    gmp_divergence_alert BOOLEAN NOT NULL DEFAULT FALSE,
    is_cross_validated BOOLEAN NOT NULL DEFAULT FALSE,
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    conflicts_json TEXT,
    sources_verified TEXT, -- JSON array e.g. ["NSE", "Chittorgarh"]
    
    -- Explicit Dual-GMP and Spread metrics
    gmp_investorgain NUMERIC(10, 2),
    gmp_ipowatch NUMERIC(10, 2),
    current_gmp_secondary NUMERIC(10, 2),
    gmp_spread VARCHAR(50),
    gmp_spread_low NUMERIC(10, 2),
    gmp_spread_high NUMERIC(10, 2),
    
    -- Audit timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Create IPO GMP History table
CREATE TABLE IF NOT EXISTS ipo_gmp (
    id BIGSERIAL PRIMARY KEY,
    ipo_id BIGINT NOT NULL REFERENCES ipos(id) ON DELETE CASCADE,
    gmp NUMERIC(10, 2) NOT NULL,
    estimated_listing_price NUMERIC(12, 2),
    estimated_gain_percent NUMERIC(6, 2),
    kostak NUMERIC(10, 2),
    subject_to_sauda NUMERIC(10, 2),
    source_name VARCHAR(100) NOT NULL,
    source_url TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Create IPO Sources Provenance table
CREATE TABLE IF NOT EXISTS ipo_sources (
    id BIGSERIAL PRIMARY KEY,
    ipo_id BIGINT NOT NULL REFERENCES ipos(id) ON DELETE CASCADE,
    source_name VARCHAR(100) NOT NULL,
    source_url TEXT,
    source_ipo_id VARCHAR(100),
    raw_data TEXT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Create Source Health Monitoring table
CREATE TABLE IF NOT EXISTS source_health (
    source_id VARCHAR(50) PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN',
    last_successful_fetch TIMESTAMPTZ,
    last_failed_fetch TIMESTAMPTZ,
    records_returned INTEGER NOT NULL DEFAULT 0,
    last_error_message TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Create Pipeline Runs Audit table
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    new_ipos_count INTEGER NOT NULL DEFAULT 0,
    updated_ipos_count INTEGER NOT NULL DEFAULT 0,
    gmp_records_count INTEGER NOT NULL DEFAULT 0,
    conflicts_count INTEGER NOT NULL DEFAULT 0,
    conflicts_summary TEXT,
    sources_summary TEXT,
    error_message TEXT
);

-- 6. Indexes for query performance and fast lookup
CREATE INDEX IF NOT EXISTS idx_ipos_slug ON ipos(slug);
CREATE INDEX IF NOT EXISTS idx_ipos_status ON ipos(status);
CREATE INDEX IF NOT EXISTS idx_ipos_type ON ipos(ipo_type);
CREATE INDEX IF NOT EXISTS idx_ipos_open_close ON ipos(open_date, close_date);
CREATE INDEX IF NOT EXISTS idx_ipos_listing_date ON ipos(listing_date);
CREATE INDEX IF NOT EXISTS idx_ipos_updated_at ON ipos(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_ipo_gmp_ipo_id_recorded ON ipo_gmp(ipo_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_ipo_gmp_recorded_at ON ipo_gmp(recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_ipo_sources_ipo_id ON ipo_sources(ipo_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_id ON pipeline_runs(id DESC);

-- 7. Supabase Row Level Security (RLS) Setup
-- Enables public read access for client apps while restricting writes
ALTER TABLE ipos ENABLE ROW LEVEL SECURITY;
ALTER TABLE ipo_gmp ENABLE ROW LEVEL SECURITY;
ALTER TABLE ipo_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_health ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read-only access
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'ipos' AND policyname = 'Public can view ipos') THEN
        CREATE POLICY "Public can view ipos" ON ipos FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'ipo_gmp' AND policyname = 'Public can view gmp') THEN
        CREATE POLICY "Public can view gmp" ON ipo_gmp FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'ipo_sources' AND policyname = 'Public can view ipo_sources') THEN
        CREATE POLICY "Public can view ipo_sources" ON ipo_sources FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'source_health' AND policyname = 'Public can view source_health') THEN
        CREATE POLICY "Public can view source_health" ON source_health FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'pipeline_runs' AND policyname = 'Public can view pipeline_runs') THEN
        CREATE POLICY "Public can view pipeline_runs" ON pipeline_runs FOR SELECT USING (true);
    END IF;
END $$;
