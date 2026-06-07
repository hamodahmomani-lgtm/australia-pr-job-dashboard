"""
Seek scraper — uses Seek's internal chalice-search JSON API.

Seek's public search page calls this endpoint from the browser.
It returns structured JSON without authentication.
"""

import logging
import time
from urllib.parse import quote_plus

from scrapers.base import BaseScraper, parse_date, parse_salary

logger = logging.getLogger(__name__)

# Seek's internal search API (called by the browser on seek.com.au)
_SEEK_API = "https://www.seek.com.au/api/chalice-search/v4/search"

# Job categories on Seek relevant to our targets
_SEEK_CLASSIFICATIONS = [
    "6251",   # Government & Defence
    "6205",   # Education & Training
    "6058",   # Healthcare & Medical
    "6092",   # Science & Technology
    "6163",   # Consulting & Strategy
    "6125",   # Information & Communication Technology
]


class SeekScraper(BaseScraper):
    name = "seek"
    source_label = "Seek"

    def __init__(self) -> None:
        super().__init__()
        # Seek requires these headers to avoid being served the SPA shell
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.seek.com.au/",
            "Origin": "https://www.seek.com.au",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        })

    def fetch(self, keywords: list[str]) -> list[dict]:
        all_jobs: list[dict] = []
        seen_ids: set[str] = set()

        for keyword in keywords:
            for page_num in range(1, 4):  # up to 3 pages per keyword
                try:
                    jobs = self._search(keyword, page=page_num)
                except Exception as exc:
                    logger.warning("Seek '%s' p%d failed: %s", keyword, page_num, exc)
                    break
                if not jobs:
                    break
                new_this_page = 0
                for j in jobs:
                    job_id = j.get("_seek_id", "")
                    if job_id and job_id not in seen_ids:
                        seen_ids.add(job_id)
                        all_jobs.append(j)
                        new_this_page += 1
                logger.info(
                    "  Seek '%s' p%d: %d jobs (%d new)",
                    keyword, page_num, len(jobs), new_this_page,
                )
                if new_this_page == 0:  # all duplicates — stop paginating
                    break
                time.sleep(2)
            time.sleep(1)

        return all_jobs

    def _search(self, keyword: str, page: int = 1) -> list[dict]:
        params = {
            "siteKey": "AU-Main",
            "keywords": keyword,
            "where": "All Australia",
            "page": str(page),
            "pageSize": "20",
            "include": "seodata",
            "sv": "jobad",
            "deviceType": "desktop",
            "locale": "en-AU",
        }
        resp = self._get(_SEEK_API, params=params)
        data = resp.json()

        if data.get("hadError") or "data" not in data:
            logger.warning("Seek API returned error for '%s': %s", keyword, data)
            return []

        jobs = []
        for item in data.get("data", []):
            job = self._normalise(item)
            if job:
                jobs.append(job)
        return jobs

    def _normalise(self, item: dict) -> dict | None:
        title = item.get("title", "").strip()
        if not title:
            return None

        org = item.get("advertiser", {}).get("description", "Unknown")
        location = item.get("location", "") or item.get("area", "")
        salary_raw = item.get("salary", "") or ""
        salary_min, salary_max = parse_salary(salary_raw)

        job_id = str(item.get("id") or item.get("jobId") or "")
        job_url = f"https://www.seek.com.au/job/{job_id}" if job_id else ""

        description = item.get("teaser", "") or item.get("shortDescription", "")
        posted_raw = item.get("listingDate", "")
        closing_raw = item.get("expiryDate", "")
        work_type = item.get("workType", "Full-time")

        job = self.make_job(
            title=title,
            organization=org,
            location=location,
            description=description,
            url=job_url,
            posted_date=posted_raw,
            closing_date=closing_raw,
            salary_min=salary_min,
            salary_max=salary_max,
            employment_type=work_type,
        )
        job["_seek_id"] = job_id
        return job
