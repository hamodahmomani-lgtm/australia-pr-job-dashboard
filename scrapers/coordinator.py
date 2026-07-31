"""
Scraper coordinator — runs all scrapers, deduplicates, saves to DB.

Usage:
    from scrapers import run_all_scrapers
    results = run_all_scrapers()   # returns summary dict
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from config import SCRAPE_SEARCH_TERMS, MAX_SCRAPER_THREADS

logger = logging.getLogger(__name__)

# Lock so multiple threads can call save_job safely
_db_lock = threading.Lock()


def run_scraper(scraper_name: str, keywords: list[str] | None = None) -> dict:
    """Run a single named scraper and save results. Returns summary."""
    from scrapers.aps_jobs    import APSJobsScraper
    from scrapers.pageup      import PageUpScraper
    from scrapers.seek        import SeekScraper
    from scrapers.consulting  import DeloitteScraper, KPMGScraper, PwCScraper, EYScraper
    from scrapers.government  import GovernmentScraper, CSIROScraper, PortalScraper
    from scrapers.import_csv  import CSVImportScraper

    # Static named scrapers
    SCRAPERS: dict[str, type] = {
        "aps_jobs":   APSJobsScraper,
        "pageup":     PageUpScraper,
        "seek":       SeekScraper,
        "deloitte":   DeloitteScraper,
        "kpmg":       KPMGScraper,
        "pwc":        PwCScraper,
        "ey":         EYScraper,
        "government": GovernmentScraper,
        "csiro":      CSIROScraper,
        "csv_import": CSVImportScraper,
    }

    # Individual per-state portal names (constructed via PortalScraper)
    _STATE_PORTAL_NAMES = {
        "nsw_government":          "NSW Government",
        "victoria_government":     "Victoria Government",
        "queensland_government":   "Queensland Government",
        "sa_government":           "SA Government",
        "wa_government":           "WA Government",
        "act_government":          "ACT Government",
        "tasmania_government":     "Tasmania Government",
        "nt_government":           "NT Government",
    }

    kws = keywords or SCRAPE_SEARCH_TERMS
    cls = SCRAPERS.get(scraper_name)
    if cls:
        scraper = cls()
        jobs = scraper.run(kws)
        new, total = _save_jobs(jobs)
        return {"scraper": scraper_name, "new": new, "total": total, "error": None}

    portal_name = _STATE_PORTAL_NAMES.get(scraper_name)
    if portal_name:
        scraper = PortalScraper(portal_name)
        jobs = scraper.run(kws)
        new, total = _save_jobs(jobs)
        return {"scraper": scraper_name, "new": new, "total": total, "error": None}

    return {"scraper": scraper_name, "error": "unknown scraper", "new": 0, "total": 0}


def run_all_scrapers(keywords: list[str] | None = None) -> dict:
    """
    Run all scrapers in parallel (up to MAX_SCRAPER_THREADS concurrent).
    Returns a summary dict with per-scraper counts.
    """
    from scrapers.aps_jobs   import APSJobsScraper
    from scrapers.pageup     import PageUpScraper
    from scrapers.seek       import SeekScraper
    from scrapers.consulting import DeloitteScraper, KPMGScraper, PwCScraper, EYScraper
    from scrapers.government import GovernmentScraper, CSIROScraper

    kws = keywords or SCRAPE_SEARCH_TERMS

    # GovernmentScraper covers all eight state/territory portals in one pass;
    # individual portal scrapers are available via run_scraper() for targeted runs.
    scraper_classes = [
        APSJobsScraper, PageUpScraper, SeekScraper,
        DeloitteScraper, KPMGScraper, PwCScraper, EYScraper,
        GovernmentScraper, CSIROScraper,
    ]

    summary = {
        "started_at": datetime.now().isoformat(),
        "scrapers": {},
        "total_new": 0,
        "total_fetched": 0,
        "errors": [],
    }

    def _run(cls):
        scraper = cls()
        jobs = scraper.run(kws)
        new, total = _save_jobs(jobs)
        return scraper.name, new, total

    with ThreadPoolExecutor(max_workers=MAX_SCRAPER_THREADS) as pool:
        futures = {pool.submit(_run, cls): cls for cls in scraper_classes}
        for future in as_completed(futures):
            try:
                name, new, total = future.result()
                summary["scrapers"][name] = {"new": new, "total": total}
                summary["total_new"] += new
                summary["total_fetched"] += total
            except Exception as exc:
                cls = futures[future]
                summary["errors"].append(f"{cls.__name__}: {exc}")
                logger.error("Scraper %s crashed: %s", cls.__name__, exc, exc_info=True)

    summary["finished_at"] = datetime.now().isoformat()
    _log_scrape_run(summary)
    logger.info(
        "Scrape complete: %d new / %d fetched in %s scrapers",
        summary["total_new"], summary["total_fetched"], len(scraper_classes),
    )
    return summary


def _save_jobs(jobs: list[dict]) -> tuple[int, int]:
    """Save jobs to DB, return (new_count, total_count)."""
    from database import save_job
    new = 0
    for job in jobs:
        with _db_lock:
            _row_id, is_new = save_job(job)
            if is_new:
                new += 1
    return new, len(jobs)


def _log_scrape_run(summary: dict) -> None:
    """Record the scrape run in the scrape_log table."""
    try:
        from database import get_connection
        import json
        conn = get_connection()
        conn.execute(
            "INSERT INTO scrape_log(started_at, finished_at, new_jobs, total_fetched, details) "
            "VALUES (?,?,?,?,?)",
            (
                summary["started_at"],
                summary.get("finished_at", ""),
                summary["total_new"],
                summary["total_fetched"],
                json.dumps(summary["scrapers"]),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning("Failed to log scrape run: %s", exc)
