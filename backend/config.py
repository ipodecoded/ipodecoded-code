import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from project root
load_dotenv(BASE_DIR / ".env")

# Database configuration
# Supabase connection URI format: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    # Default to local sqlite file for seamless out-of-the-box local testing
    SQLITE_PATH = BASE_DIR / "ipodecoded.db"
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
elif DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy requires postgresql:// dialect prefix instead of legacy postgres://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Supabase REST client configuration (optional if using direct DB or frontend Supabase JS)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Server configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS")
if CORS_ORIGINS_ENV:
    CORS_ORIGINS = [orig.strip() for orig in CORS_ORIGINS_ENV.split(",") if orig.strip()]
else:
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://ipodecoded.vercel.app",
        "https://ipodecoded.journaldecoded.in",
        "*"
    ]

# Pipeline settings
SCRAPER_USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 IPODecoded/1.0 (JournalDecoded.in)"
)
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", 15))
IPO_FETCH_INTERVAL_HOURS = int(os.getenv("IPO_FETCH_INTERVAL_HOURS", 2))
GMP_FETCH_INTERVAL_MINUTES = int(os.getenv("GMP_FETCH_INTERVAL_MINUTES", 45))
