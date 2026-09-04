# IPODecoded (A JournalDecoded.in Product)

> **Automatic Indian IPO Intelligence, Issue Timetables, Subscription Multiples & Live Grey Market Premium (GMP) Tracking.**

---

## ⚡ Quick Run (Local Development)

To start both the FastAPI backend and Vite frontend with a single command:
```bash
./start.sh
```
See the full step-by-step guide in [HOW_TO_RUN.md](HOW_TO_RUN.md) or [HOW_TO_RUN.txt](HOW_TO_RUN.txt).

---

## 🎯 Project Overview

**IPODecoded** is a zero-cost, production-ready MVP built as a subsidiary and product of **JournalDecoded.in**.

The platform is designed around one primary objective: **AUTOMATIC IPO DATA COLLECTION AND DISPLAY**.
No manual data entry is required. The system periodically checks reliable public sources, detects new announcements and modifications to existing issues (price bands, dates, lot sizes, subscription numbers), calculates estimated listing gains, records day-by-day GMP histories, and updates the website automatically.

### V1 Core Philosophy: Zero Overengineering
- ❌ No AI agents / LangChain / RAG / Vector databases
- ❌ No machine learning models
- ❌ No paid scraping APIs
- ❌ No unnecessary authentication or payment systems
- ❌ Zero infrastructure cost (target: ₹0/month)
- ✅ Deterministic, resilient, modular parsers with fallback datasets
- ✅ Strict validation & change detection (never wipes valid existing data with nulls)
- ✅ Clean, responsive, high-density Indian financial UI

---

## 🏗️ Architecture & Data Flow

```
+-------------------------------------------------------------------------+
|                         PUBLIC IPO DATA SOURCES                         |
|   (BSE / NSE Portals, SEBI DRHP, Chittorgarh, InvestorGain Live GMP)    |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                      AUTOMATED PYTHON DATA PIPELINE                     |
|  1. Fetcher: Requests / HTTPX with browser headers & timeout handling   |
|  2. Modular Adapters: sources/chittorgarh_adapter.py, investorgain.py   |
|  3. Normalizer: Indian dates (DD-MMM-YYYY), price bands, lot metrics    |
|  4. Validator: pipeline/validator.py (Rejects dirty/negative data)      |
|  5. Upsert Engine: pipeline/upsert.py (Idempotent, change-detecting)    |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  POSTGRESQL / SUPABASE (FREE TIER)                      |
|  - Table: `ipos` (Metadata, timetable dates, issue size, subscription)  |
|  - Table: `ipo_gmp` (Day-by-day GMP trajectory & source audit history)  |
|  - Indexes: Slug, Status, Type, Open/Close dates, GMP recorded_at       |
|  - RLS: Public read access enabled                                      |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                       MINIMAL FASTAPI BACKEND API                       |
|  - GET /api/ipos               (Filtered by status, segment, search)    |
|  - GET /api/ipos/{slug}        (Full IPO profile & latest metrics)      |
|  - GET /api/ipos/{slug}/gmp-history (Timeline trajectory data)          |
|  - GET /api/stats              (Market pulse: active, open, top gainers)|
|  - POST /api/pipeline/run      (On-demand automated sync trigger)       |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                    REACT + VITE + TAILWIND CSS FRONTEND                 |
|  - Dashboard: Currently Open, Upcoming, Closed, Listed segments         |
|  - Directory / Screener: Multi-facet filters, search, grid/table toggle |
|  - Detail View: Issue Timetable progression, KPI cards, SVG GMP chart   |
|  - SEO: Dynamic titles, Open Graph tags, sitemap.xml, robots.txt        |
+-------------------------------------------------------------------------+
```

---

## 📊 Database Schema

### 1. `ipos` Table
Maintains the canonical state of each Indian IPO.
```sql
CREATE TABLE ipos (
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
    
    -- Company description & Source tracking
    company_description TEXT,
    source_name VARCHAR(100),
    source_url TEXT,
    source_id VARCHAR(100),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2. `ipo_gmp` Table (History Tracking)
Maintains historical progression of Grey Market Premiums over time.
```sql
CREATE TABLE ipo_gmp (
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
```

### GMP Formulas
- **Estimated Listing Price** = Upper Price Band + Current GMP
- **Estimated Listing Gain %** = `(Current GMP / Upper Price Band) * 100`

---

## ⚡ Quick Start (Local Development)

### Method A: One-Click Startup
From the project root:
```bash
./start.sh
```
This activates the virtual environment, initializes the database, starts the FastAPI backend at `http://localhost:8000`, and starts the Vite frontend at `http://localhost:5173`.

### Method B: Manual Startup

#### 1. Setup Python Backend & Data Pipeline
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Run initial ingestion cycle
python -m pipeline.runner

# Start FastAPI API server
uvicorn backend.main:app --reload --port 8000
```

#### 2. Setup React Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Running Automated Tests

Run the full test suite verifying validation rules, date parsers, change detection, idempotent upserts, GMP history tracking, and API endpoints:
```bash
python -m unittest discover -s tests
```
*(All 13 test cases run in < 0.3s)*

---

## 🚀 Free ₹0/Month Production Deployment Guide

### Step 1: Database Setup (Supabase Free PostgreSQL)
1. Go to [Supabase](https://supabase.com) and create a free project.
2. Open the **SQL Editor** in your Supabase dashboard.
3. Paste the contents of `database/schema.sql` and click **Run**.
4. Copy your PostgreSQL connection URI from **Project Settings > Database > Connection string (URI)**:
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

### Step 2: Automated 2-Hour Ingestion (GitHub Actions Cron)
The repository includes `.github/workflows/scrape-ipos.yml`.
1. Push your repository to GitHub.
2. Go to **Settings > Secrets and variables > Actions > New repository secret**.
3. Add:
   - `DATABASE_URL`: Your Supabase connection string.
4. The workflow will run automatically every 2 hours at minute 0, or whenever you click **Run workflow** in the GitHub Actions tab!

### Step 3: Frontend Deployment (Vercel / Netlify Free Tier)
Deploying to Vercel:
1. Import your Git repository in [Vercel](https://vercel.com).
2. Set Framework Preset to **Vite**.
3. Set Root Directory to `frontend`.
4. Set Environment Variable:
   - `VITE_API_URL`: URL of your deployed backend or Supabase PostgREST endpoint.
5. Deploy!

---

## ⚖️ Statutory Disclaimer

> **IPODecoded** (a product of **JournalDecoded.in**) provides IPO information for educational and informational purposes only. Grey Market Premium (GMP) is unofficial, unregulated, and may change dynamically. Estimated listing gains are mathematical projections and do not guarantee actual exchange listing performance. Always consult official SEBI, BSE, and NSE prospectuses before making investment decisions.
