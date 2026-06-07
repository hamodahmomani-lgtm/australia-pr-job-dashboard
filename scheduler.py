"""
Daily job refresh scheduler.

Uses APScheduler (BackgroundScheduler) so it runs in a daemon thread
alongside the Streamlit process. Safe to call start() multiple times —
subsequent calls are no-ops once the scheduler is running.

Usage:
    from scheduler import start_scheduler, stop_scheduler
    start_scheduler()   # call once at app startup
"""

import logging
import threading
from datetime import datetime

from config import SCRAPE_HOUR, SCRAPE_MINUTE

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_scheduler = None


def _refresh_job():
    """The function APScheduler calls on the daily trigger."""
    logger.info("Scheduled scrape started at %s", datetime.now().isoformat())
    try:
        from scrapers.coordinator import run_all_scrapers
        from notifier import send_scrape_summary, send_new_jobs_alert
        from database import get_jobs

        # Snapshot job IDs before scrape
        before_ids = {j["id"] for j in get_jobs(limit=10_000)}

        summary = run_all_scrapers()

        # Find genuinely new jobs (not previously in DB)
        after_jobs = get_jobs(limit=10_000)
        new_jobs = [j for j in after_jobs if j["id"] not in before_ids]

        send_scrape_summary(summary)
        if new_jobs:
            send_new_jobs_alert(new_jobs)

        # Check for follow-ups due today
        _send_followup_reminders()

        logger.info(
            "Scheduled scrape done: %d new / %d total",
            summary["total_new"], summary["total_fetched"],
        )
    except Exception as exc:
        logger.error("Scheduled scrape failed: %s", exc, exc_info=True)


def _send_followup_reminders():
    """Send Telegram reminders for applications with a follow-up due today."""
    try:
        from database import get_applications
        from notifier import send_application_reminder
        from datetime import date
        today = date.today().isoformat()
        for app in get_applications():
            if app.get("follow_up_date") == today:
                send_application_reminder(app)
    except Exception as exc:
        logger.warning("Follow-up reminder failed: %s", exc)


def start_scheduler() -> bool:
    """
    Start the background scheduler if APScheduler is installed.
    Returns True if scheduler is running, False if APScheduler not installed.
    """
    global _scheduler
    with _lock:
        if _scheduler is not None and _scheduler.running:
            return True
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            logger.warning(
                "APScheduler not installed — daily refresh disabled. "
                "Install with: pip install apscheduler"
            )
            return False

        _scheduler = BackgroundScheduler(
            job_defaults={"coalesce": True, "max_instances": 1},
            timezone="Australia/Canberra",
        )
        _scheduler.add_job(
            _refresh_job,
            CronTrigger(hour=SCRAPE_HOUR, minute=SCRAPE_MINUTE),
            id="daily_scrape",
            name="Daily job scrape",
            replace_existing=True,
        )
        _scheduler.start()
        logger.info(
            "Scheduler started — daily scrape at %02d:%02d AEST",
            SCRAPE_HOUR, SCRAPE_MINUTE,
        )
        return True


def stop_scheduler() -> None:
    global _scheduler
    with _lock:
        if _scheduler and _scheduler.running:
            _scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")


def get_next_run_time() -> str:
    """Return a human-readable next-run time, or empty string if not running."""
    global _scheduler
    if not _scheduler or not _scheduler.running:
        return ""
    job = _scheduler.get_job("daily_scrape")
    if not job or not job.next_run_time:
        return ""
    return job.next_run_time.strftime("%Y-%m-%d %H:%M %Z")


def scheduler_running() -> bool:
    global _scheduler
    return bool(_scheduler and _scheduler.running)
