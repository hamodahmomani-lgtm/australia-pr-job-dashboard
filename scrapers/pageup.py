"""
PageUp university scraper.

Most Group of Eight and other major Australian universities run PageUp.
Their listing pages share a consistent HTML structure we can rely on.
"""

import logging
import re
import time
from urllib.parse import urljoin, urlencode

from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, parse_date, parse_salary, today

logger = logging.getLogger(__name__)

# ── Known Australian university PageUp portals ────────────────────────────────
# Format: (display_name, base_listing_url)
UNIVERSITY_PORTALS = [
    ("Australian National University",         "https://jobs.anu.edu.au/cw/en/listing/"),
    ("University of Melbourne",                "https://jobs.unimelb.edu.au/cw/en/listing/"),
    ("University of New South Wales",          "https://www.jobs.unsw.edu.au/cw/en/listing/"),
    ("University of Queensland",               "https://careers.uq.edu.au/cw/en/listing/"),
    ("Monash University",                      "https://careers.pageuppeople.com/513/cw/en/listing/"),
    ("University of Sydney",                   "https://usyd.pageuppeople.com/cw/en/listing/"),
    ("University of Adelaide",                 "https://careers.adelaide.edu.au/cw/en/listing/"),
    ("University of Western Australia",        "https://jobs.uwa.edu.au/cw/en/listing/"),
    ("University of Technology Sydney",        "https://careers.uts.edu.au/cw/en/listing/"),
    ("Macquarie University",                   "https://jobs.mq.edu.au/cw/en/listing/"),
    ("University of Canberra",                 "https://jobs.canberra.edu.au/cw/en/listing/"),
    ("Australian Catholic University",         "https://jobs.acu.edu.au/cw/en/listing/"),
    ("Curtin University",                      "https://careers.pageuppeople.com/972/cw/en/listing/"),
    ("Flinders University",                    "https://careers.flinders.edu.au/cw/en/listing/"),
    ("RMIT University",                        "https://careers.pageuppeople.com/764/cw/en/listing/"),
    ("Deakin University",                      "https://careers.deakin.edu.au/cw/en/listing/"),
    ("Griffith University",                    "https://careers.griffith.edu.au/cw/en/listing/"),
    ("La Trobe University",                    "https://careers.pageuppeople.com/523/cw/en/listing/"),
    ("CSIRO",                                  "https://jobs.csiro.au/cw/en/listing/"),
    ("Australian Institute of Health and Welfare", "https://www.apsjobs.gov.au/s/search"),  # APS portal
]

# Keywords that must appear in title or description to be included
_RELEVANT_TERMS = [
    "economist", "economics", "policy", "evaluation", "data analyst",
    "research fellow", "lecturer", "tutor", "business intelligence",
    "postdoctoral", "post-doc", "health", "social", "public",
    "quantitative", "analytical", "statistician", "epidemiologist",
]


def _is_relevant(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    return any(term in text for term in _RELEVANT_TERMS)


class PageUpScraper(BaseScraper):
    name = "pageup"
    source_label = "University Portal"

    def fetch(self, keywords: list[str]) -> list[dict]:
        all_jobs: list[dict] = []
        for org_name, base_url in UNIVERSITY_PORTALS:
            if "apsjobs" in base_url:
                continue  # APS handled separately
            try:
                jobs = self._scrape_portal(org_name, base_url, keywords)
                all_jobs.extend(jobs)
                logger.info("  %s: %d jobs", org_name, len(jobs))
            except Exception as exc:
                logger.warning("PageUp %s failed: %s", org_name, exc)
            time.sleep(1.5)
        return all_jobs

    def _scrape_portal(self, org_name: str, base_url: str, keywords: list[str]) -> list[dict]:
        """Scrape a PageUp portal (up to 3 pages), filter by keywords, enrich top results."""
        jobs: list[dict] = []
        seen_urls: set[str] = set()
        page_url = base_url

        for _page in range(3):  # max 3 pages per portal
            resp = self._get(page_url, headers={"Referer": base_url})
            soup = BeautifulSoup(resp.text, "html.parser")

            items = soup.select("li.lv-item, article.lv-item-container")
            if not items:
                items = soup.select(".job-listing, .position-item, .vacancy-item")

            page_had_new = False
            for item in items:
                job = self._parse_item(item, org_name, base_url)
                if not job or job["url"] in seen_urls:
                    continue
                seen_urls.add(job["url"])
                if _is_relevant(job["title"], job.get("description", "")):
                    jobs.append(job)
                    page_had_new = True

            if not page_had_new:
                break

            next_url = self._get_next_page(soup, base_url)
            if not next_url or next_url == page_url:
                break
            page_url = next_url
            time.sleep(1.5)

        # Enrich up to 5 results that have a specific job URL (fetch full description)
        to_enrich = [j for j in jobs if j.get("url") and j["url"] != base_url][:5]
        for job in to_enrich:
            full_desc, reqs = self.fetch_job_detail(job["url"])
            if full_desc:
                job["description"] = full_desc[:1500]
            if reqs:
                job["requirements"] = reqs[:500]
            time.sleep(1)

        return jobs

    def _get_next_page(self, soup: BeautifulSoup, base_url: str) -> str | None:
        """Return the next-page URL from PageUp pagination controls, or None."""
        next_el = soup.select_one(
            "a.lv-pagination-next, a[class*='pagination-next'], "
            "li.next > a, [aria-label='Next page' i], "
            "[class*='pagination'] a[rel='next']"
        )
        if not next_el:
            return None
        href = next_el.get("href", "")
        return urljoin(base_url, href) if href else None

    def _parse_item(self, item, org_name: str, base_url: str) -> dict | None:
        # Title — PageUp puts title in h3.lv-item-title > a
        title_el = (
            item.select_one("h3.lv-item-title a")
            or item.select_one("h2 a, h3 a, h4 a")
            or item.select_one(".job-title a, .position-title a")
        )
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        # URL
        href = title_el.get("href", "")
        job_url = urljoin(base_url, href) if href else base_url

        # Location
        loc_el = item.select_one(
            "li.lv-item-location, .lv-item-location, "
            "[class*='location'], [class*='campus']"
        )
        location = loc_el.get_text(strip=True) if loc_el else org_name

        # Closing date
        close_el = item.select_one(
            "p.lv-item-closing, .lv-item-closing, "
            "[class*='closing'], [class*='close-date']"
        )
        close_raw = close_el.get_text(strip=True) if close_el else ""
        # Strip label text like "Applications close:"
        close_raw = re.sub(r"[Aa]pplications?\s+(close[sd]?:?|by:?)", "", close_raw).strip()

        # Department / category hint
        dept_el = item.select_one(
            "li.lv-item-category, .lv-item-list li:first-child, "
            "[class*='department'], [class*='faculty']"
        )
        dept = dept_el.get_text(strip=True) if dept_el else ""

        # Short description (teaser)
        desc_el = item.select_one(
            "p.lv-item-teaser, .lv-item-description, "
            "[class*='teaser'], [class*='summary']"
        )
        description = desc_el.get_text(strip=True) if desc_el else dept

        return self.make_job(
            title=title,
            organization=org_name,
            location=location if location else org_name,
            description=description,
            url=job_url,
            closing_date=close_raw,
        )

    def fetch_job_detail(self, job_url: str) -> tuple[str, str]:
        """Fetch full description and requirements from a job detail page."""
        try:
            resp = self._get(job_url)
            soup = BeautifulSoup(resp.text, "html.parser")

            # PageUp job detail uses .job-description or #job-description
            desc_el = soup.select_one(
                "#job-description, .job-description, "
                "[class*='job-detail'], .position-description, main article"
            )
            if not desc_el:
                return "", ""

            full_text = desc_el.get_text(separator="\n", strip=True)

            # Split into description and requirements heuristically
            req_patterns = r"(requirements?|qualifications?|what you.ll need|selection criteria)"
            parts = re.split(req_patterns, full_text, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) > 1:
                return parts[0].strip(), (parts[1] + parts[2]).strip() if len(parts) > 2 else parts[1].strip()
            return full_text, ""
        except Exception:
            return "", ""
