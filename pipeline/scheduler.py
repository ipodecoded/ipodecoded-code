import time
import signal
import sys
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from backend.config import IPO_FETCH_INTERVAL_HOURS, GMP_FETCH_INTERVAL_MINUTES
from pipeline.runner import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [Scheduler] %(message)s"
)
logger = logging.getLogger("ipodecoded.scheduler")

def scheduled_job():
    logger.info("Executing scheduled IPO & GMP collection cycle...")
    try:
        summary = run_pipeline()
        logger.info(f"Scheduled cycle completed: {summary['new_ipos']} new, {summary['updated_ipos']} updated, {summary['gmp_records_added']} GMP additions.")
    except Exception as e:
        logger.error(f"Error in scheduled job: {e}")

def main():
    scheduler = BlockingScheduler()

    # Schedule regular full ingestion cycle
    scheduler.add_job(
        scheduled_job,
        'interval',
        hours=IPO_FETCH_INTERVAL_HOURS,
        id='ipo_pipeline_job',
        next_run_time=None # Will run after the first initial run below
    )

    logger.info(f"Scheduler initialized: running pipeline every {IPO_FETCH_INTERVAL_HOURS} hours.")

    # Graceful shutdown handler
    def handle_exit(signum, frame):
        logger.info("Shutdown signal received. Stopping scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Run once immediately on launch
    scheduled_job()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()
