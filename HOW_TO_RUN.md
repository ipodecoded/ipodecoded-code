# How to Run IPODecoded

Quick reference guide to run the IPODecoded frontend, backend, live data pipeline, and tests locally.

---

## ⚡ Option 1: Quick Start (Single Command)

We have included a launcher script that starts the database check, FastAPI backend, and Vite frontend together:

```bash
./start.sh
```

- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **FastAPI API & Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- Press `Ctrl + C` in your terminal to gracefully stop both servers.

---

## 🛠️ Option 2: Step-by-Step Manual Start

If you prefer to run the backend and frontend in separate terminal windows:

### Terminal 1: Backend (FastAPI on Port 8000)

```bash
# 1. Activate the Python virtual environment
source venv/bin/activate

# 2. (Optional) Install dependencies if needed
pip install -r backend/requirements.txt

# 3. Start the FastAPI development server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend endpoints:
- Swagger Interactive UI: `http://localhost:8000/docs`
- Root info: `http://localhost:8000/`
- IPO listing: `http://localhost:8000/api/ipos`
- Sources health & provenance: `http://localhost:8000/api/sources/health`
- GMP conflicts audit: `http://localhost:8000/api/pipeline/conflicts`

---

### Terminal 2: Frontend (Vite + React on Port 5173)

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. (Optional) Install node modules if needed
npm install

# 3. Start Vite dev server
npm run dev
```

Frontend application will be live at:
- `http://localhost:5173`

---

## 🔄 How to Run the Live Ingestion Pipeline Manually

IPODecoded uses a live multi-source pipeline (NSE India + Chittorgarh for master IPO data, and InvestorGain + IPOWatch for dual GMP tracking).

To fetch, reconcile, cross-validate, and update the database on demand:

```bash
source venv/bin/activate
python -m pipeline.runner
```

Or trigger it via the backend API:
```bash
curl -X POST http://localhost:8000/api/pipeline/run
```

---

## 🐘 How to Migrate SQLite Data to PostgreSQL / Neon

To migrate all 213 live IPOs, GMP history, and provenance records to your Neon PostgreSQL database without modifying or deleting your local SQLite database:

```bash
source venv/bin/activate
python scripts/migrate_sqlite_to_postgres.py "postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"
```

---

## 🧪 How to Run Automated Tests

To run the complete unit test suite (25 tests covering validation, adapters, models, scheduler, and API endpoints):

```bash
source venv/bin/activate
python -m unittest discover tests
```

---

## 📁 Key File Locations

- **Logo file**: `ipo-decoded-image.png` (root folder) & `frontend/public/ipo-decoded-logo.png`
- **Favicons**: `frontend/public/favicon.ico`, `favicon-32x32.png`, `favicon-192x192.png`
- **Database file**: `ipodecoded.db` (SQLite)
- **Environment config**: `.env`
