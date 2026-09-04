import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc, case
from apscheduler.schedulers.background import BackgroundScheduler

from backend.config import CORS_ORIGINS, IPO_FETCH_INTERVAL_HOURS
from backend.db import get_db, init_db, IPO, IPOGMP, SourceHealth, PipelineRun, IPOSource
from backend.schemas import (
    IPOSummarySchema, IPOListResponse, GMPRecordSchema, StatsResponse,
    SourceHealthSchema, PipelineRunSchema
)
from pipeline.runner import run_pipeline

logger = logging.getLogger("ipodecoded.api")

# Initialize database schema if not present
init_db()

# Automatic Background Pipeline Scheduler
scheduler = BackgroundScheduler(daemon=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the automatic background pipeline scheduler
    try:
        scheduler.add_job(
            run_pipeline,
            'interval',
            hours=IPO_FETCH_INTERVAL_HOURS,
            id='auto_pipeline_job',
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"[Scheduler] BackgroundScheduler active: scheduled to run every {IPO_FETCH_INTERVAL_HOURS} hours.")
    except Exception as e:
        logger.error(f"[Scheduler] Failed to start BackgroundScheduler: {e}")

    yield

    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("[Scheduler] BackgroundScheduler shut down cleanly.")
    except Exception as e:
        logger.error(f"[Scheduler] Error shutting down BackgroundScheduler: {e}")

app = FastAPI(
    title="IPODecoded API",
    description="Multi-Source Indian IPO Intelligence and Grey Market Premium API for JournalDecoded.in",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root_info():
    """
    Root endpoint providing API metadata, status, and link to documentation.
    """
    return {
        "name": "IPODecoded API",
        "description": "Multi-Source Indian IPO Intelligence and Grey Market Premium API",
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs",
        "endpoints": {
            "health": "/api/health",
            "scheduler": "/api/scheduler/status",
            "ipos": "/api/ipos",
            "stats": "/api/stats",
            "sources_health": "/api/sources/health",
            "pipeline_conflicts": "/api/pipeline/conflicts",
            "pipeline_runs": "/api/pipeline/runs",
            "sitemap": "/api/sitemap.xml"
        }
    }

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Run lightweight query to confirm DB connection
        ipo_count = db.query(IPO).count()
        return {
            "status": "healthy",
            "database": "connected",
            "ipo_count": ipo_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database_error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/api/scheduler/status")
def get_scheduler_status():
    """
    Returns the real-time operational status of the automatic background pipeline scheduler.
    """
    jobs = []
    if scheduler.running:
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "interval_hours": IPO_FETCH_INTERVAL_HOURS
            })
    return {
        "is_running": scheduler.running,
        "interval_hours": IPO_FETCH_INTERVAL_HOURS,
        "active_jobs_count": len(jobs),
        "jobs": jobs
    }

@app.get("/api/sources/health", response_model=List[SourceHealthSchema])
def get_sources_health(db: Session = Depends(get_db)):
    """
    Returns live health, latency, and ingestion status of all 4 data sources:
    NSE, Chittorgarh, InvestorGain, and IPOWatch.
    """
    records = db.query(SourceHealth).all()
    return [r.to_dict() for r in records]

@app.get("/api/pipeline/conflicts")
def get_pipeline_conflicts(db: Session = Depends(get_db)):
    """
    Returns logged cross-source conflicts between official exchanges and secondary sources.
    """
    latest_run = db.query(PipelineRun).order_by(desc(PipelineRun.id)).first()
    if not latest_run:
        return {"conflicts_count": 0, "conflicts": []}

    run_dict = latest_run.to_dict()
    return {
        "run_id": latest_run.id,
        "run_status": latest_run.status,
        "completed_at": latest_run.completed_at.isoformat() if latest_run.completed_at else None,
        "conflicts_count": latest_run.conflicts_count,
        "conflicts": run_dict.get("conflicts_summary") or []
    }

@app.get("/api/pipeline/runs", response_model=List[PipelineRunSchema])
def get_pipeline_runs(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """
    Returns audit trail of recent pipeline runs.
    """
    runs = db.query(PipelineRun).order_by(desc(PipelineRun.id)).limit(limit).all()
    return [r.to_dict() for r in runs]

@app.get("/api/ipos", response_model=IPOListResponse)
def list_ipos(
    status: Optional[str] = Query(None, description="Filter by status: Upcoming, Open, Closed, Listed"),
    ipo_type: Optional[str] = Query(None, description="Filter by type: Mainboard, SME"),
    search: Optional[str] = Query(None, description="Search query by company name"),
    sort_by: Optional[str] = Query("default", description="Sort criteria: default, date_asc, date_desc, size_desc, name_asc"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(IPO)

    # Filter by Status
    if status and status.lower() != "all":
        status_norm = status.capitalize()
        query = query.filter(IPO.status == status_norm)

    # Filter by IPO Type
    if ipo_type and ipo_type.lower() != "all":
        ipo_type_norm = "Mainboard" if ipo_type.lower() == "mainboard" else "SME"
        query = query.filter(IPO.ipo_type == ipo_type_norm)

    # Search filter
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                IPO.company_name.ilike(search_term),
                IPO.slug.ilike(search_term)
            )
        )

    # Sorting logic
    if sort_by == "date_asc":
        query = query.order_by(asc(IPO.open_date).nullslast(), asc(IPO.close_date).nullslast())
    elif sort_by == "date_desc":
        query = query.order_by(desc(IPO.open_date).nullsfirst(), desc(IPO.close_date).nullsfirst())
    elif sort_by == "size_desc":
        query = query.order_by(desc(IPO.issue_size).nullslast())
    elif sort_by == "name_asc":
        query = query.order_by(asc(IPO.company_name))
    else:
        # Default smart priority sorting:
        # Open IPOs first, then Upcoming, then Recently Closed, then Listed
        # Within each, order by open_date or close_date
        query = query.order_by(
            case(
                (IPO.status == 'Open', 1),
                (IPO.status == 'Upcoming', 2),
                (IPO.status == 'Closed', 3),
                (IPO.status == 'Listed', 4),
                else_=5
            ),
            desc(IPO.close_date).nullslast(),
            desc(IPO.open_date).nullslast(),
            desc(IPO.id)
        )

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return IPOListResponse(
        total=total,
        items=[ipo.to_dict() for ipo in items]
    )

@app.get("/api/ipos/{slug}", response_model=IPOSummarySchema)
def get_ipo_by_slug(slug: str, db: Session = Depends(get_db)):
    ipo = db.query(IPO).filter(IPO.slug == slug).first()
    if not ipo:
        # Try finding by partial slug match
        ipo = db.query(IPO).filter(IPO.slug.ilike(f"%{slug}%")).first()
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO with slug '{slug}' not found")

    return ipo.to_dict()

@app.get("/api/ipos/{slug}/sources")
def get_ipo_sources(slug: str, db: Session = Depends(get_db)):
    """
    Returns full provenance and contributing sources for a specific IPO.
    """
    ipo = db.query(IPO).filter(IPO.slug == slug).first()
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO with slug '{slug}' not found")

    sources = db.query(IPOSource).filter(IPOSource.ipo_id == ipo.id).all()
    return {
        "ipo_id": ipo.id,
        "company_name": ipo.company_name,
        "sources": [s.to_dict() for s in sources]
    }

@app.get("/api/ipos/{slug}/gmp-history", response_model=List[GMPRecordSchema])
def get_gmp_history(slug: str, db: Session = Depends(get_db)):
    ipo = db.query(IPO).filter(IPO.slug == slug).first()
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO with slug '{slug}' not found")

    records = db.query(IPOGMP).filter(IPOGMP.ipo_id == ipo.id).order_by(asc(IPOGMP.recorded_at)).all()
    return [r.to_dict() for r in records]

@app.get("/api/stats", response_model=StatsResponse)
def get_market_stats(db: Session = Depends(get_db)):
    open_count = db.query(IPO).filter(IPO.status == "Open").count()
    upcoming_count = db.query(IPO).filter(IPO.status == "Upcoming").count()
    closed_count = db.query(IPO).filter(IPO.status == "Closed").count()
    listed_count = db.query(IPO).filter(IPO.status == "Listed").count()
    mainboard_count = db.query(IPO).filter(IPO.ipo_type == "Mainboard").count()
    sme_count = db.query(IPO).filter(IPO.ipo_type == "SME").count()

    # Get active IPOs with GMP for top gainers
    active_ipos = db.query(IPO).filter(IPO.status.in_(["Open", "Upcoming"])).all()

    # Sort by estimated_gain_percent descending
    gainers = []
    for item in active_ipos:
        item_dict = item.to_dict()
        if item_dict.get("estimated_gain_percent") is not None:
            gainers.append(item_dict)

    gainers.sort(key=lambda x: x["estimated_gain_percent"], reverse=True)
    top_gainers = gainers[:5]

    return StatsResponse(
        total_active_ipos=open_count + upcoming_count,
        open_ipos_count=open_count,
        upcoming_ipos_count=upcoming_count,
        recently_closed_count=closed_count,
        recently_listed_count=listed_count,
        mainboard_count=mainboard_count,
        sme_count=sme_count,
        top_gmp_gainers=top_gainers
    )

@app.post("/api/pipeline/run")
def trigger_pipeline(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Manually triggers the multi-source live ingestion pipeline.
    Runs synchronously and returns execution metrics and conflict summary.
    """
    from pipeline.runner import run_pipeline

    summary = run_pipeline(db)
    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary
    }

@app.get("/sitemap.xml", response_class=Response)
@app.get("/api/sitemap.xml", response_class=Response)
def get_dynamic_sitemap(db: Session = Depends(get_db)):
    """
    Dynamically generates XML sitemap containing all active IPO slugs for search engine indexing.
    """
    site_url = "https://ipodecoded.journaldecoded.in"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ipos = db.query(IPO).all()

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <url><loc>{site_url}/</loc><lastmod>{now_iso}</lastmod><changefreq>hourly</changefreq><priority>1.0</priority></url>',
        f'  <url><loc>{site_url}/ipos</loc><lastmod>{now_iso}</lastmod><changefreq>hourly</changefreq><priority>0.9</priority></url>',
    ]

    for ipo in ipos:
        lastmod = ipo.updated_at.strftime("%Y-%m-%d") if ipo.updated_at else now_iso
        xml_lines.append(
            f'  <url><loc>{site_url}/ipo/{ipo.slug}</loc><lastmod>{lastmod}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>'
        )

    xml_lines.append('</urlset>')
    content = "\n".join(xml_lines)
    return Response(content=content, media_type="application/xml")
