"""
Government portal scrapers — all eight state/territory governments + CSIRO.

All government portals are JavaScript-rendered SPAs (React/Angular/Vue).
requests.get() returns only the SPA shell; Playwright is required.
CSIRO uses the same PageUp server-rendered portal as the universities.

Each portal produces jobs tagged with a per-state source label so the
Browse Jobs source filter shows individual state options.

Portal health is tracked in PORTAL_STATUS (module-level dict).  The smoke
test (smoke_test.py) reads this dict to report Working / Blocked / Error.
"""

import logging
import time
from urllib.parse import urljoin, urlencode

from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, parse_date, parse_salary, today

logger = logging.getLogger(__name__)


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


# ── Portal definitions ────────────────────────────────────────────────────────
# source_label must match an entry in config.JOB_SOURCES so it appears in the
# Browse Jobs source filter.

_GOV_PORTALS: list[dict] = [
    {
        "name": "NSW Government",
        "state": "NSW",
        "search_url": "https://iworkfor.nsw.gov.au/jobs/search",
        "params": lambda kw: {"keyword": kw},
        "wait_sel": "[class*='vacancy'], [class*='job-result'], article",
    },
    {
        "name": "Victoria Government",
        "state": "VIC",
        "search_url": "https://careers.vic.gov.au/jobs",
        "params": lambda kw: {"keyword": kw},
        "wait_sel": "[class*='job-card'], [class*='vacancy-listing']",
    },
    {
        "name": "Queensland Government",
        "state": "QLD",
        "search_url": "https://www.workinqueensland.qld.gov.au/en/Find-a-role",
        "params": lambda kw: {"keywords": kw},
        "wait_sel": "[class*='job-item'], [class*='result-item']",
    },
    {
        "name": "SA Government",
        "state": "SA",
        "search_url": "https://www.sagovernmentjobs.sa.gov.au/search",
        "params": lambda kw: {"keywords": kw},
        "wait_sel": "[class*='vacancy'], article",
    },
    {
        "name": "WA Government",
        "state": "WA",
        "search_url": "https://jobs.wa.gov.au/web/Search",
        "params": lambda kw: {"keyword": kw},
        "wait_sel": ".job-item, .search-result, [class*='result']",
    },
    {
        "name": "ACT Government",
        "state": "ACT",
        "search_url": "https://www.jobs.act.gov.au/jobs",
        "params": lambda kw: {"keyword": kw},
        "wait_sel": "[class*='job-listing'], [class*='vacancy-item']",
    },
    {
        "name": "Tasmania Government",
        "state": "TAS",
        "search_url": "https://jobs.tas.gov.au/search",
        "params": lambda kw: {"keyword": kw},
        "wait_sel": "[class*='job'], [class*='vacancy'], article, .listing",
    },
    {
        "name": "NT Government",
        "state": "NT",
        "search_url": "https://jobs.nt.gov.au/search",
        "params": lambda kw: {"Keywords": kw},
        "wait_sel": "[class*='job'], [class*='vacancy'], article",
    },
]

# Track scraping health for each portal.
# Values: "unknown" | "ok" | "partial" | "blocked" | "error"
PORTAL_STATUS: dict[str, str] = {p["name"]: "unknown" for p in _GOV_PORTALS}

_RELEVANT_TERMS = [
    # Standard roles
    "economist", "economics", "policy", "analyst", "evaluation",
    "research", "data", "intelligence", "lecturer", "statistician",
    "health", "social", "finance", "treasury", "public service",
    # Target role titles
    "policy officer", "policy analyst", "senior policy", "research officer",
    "evaluation officer", "program evaluation", "health policy",
    "data analyst", "business intelligence", "health economist",
    "government research", "program officer",
    # Domain terms
    "ageing", "aged care", "wellbeing", "preventive", "disability",
    "community", "environment", "infrastructure", "planning",
]


def _is_relevant(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in _RELEVANT_TERMS)


# ── Generic DOM-extraction JS ─────────────────────────────────────────────────
# Works against React/Angular/Vue SPA portals once they've fully rendered.

_EXTRACT_JS = """
() => {
    const results = [];
    const seen = new Set();

    const CONTAINER_SELS = [
        'article', 'li[class*="job"]', 'li[class*="vacancy"]',
        'li[class*="result"]', 'div[class*="job-result"]',
        'div[class*="vacancy-item"]', 'div[class*="result-item"]',
        '[data-automation*="job"]', 'tr[class*="result"]',
    ];
    const TITLE_SELS = [
        'h2 a', 'h3 a', 'h4 a',
        'a[class*="title"]', 'a[class*="job"]',
        '[class*="title"] a', 'a',
    ];
    const LOC_SELS   = ['[class*="location"]', '[class*="suburb"]', '[class*="city"]'];
    const SAL_SELS   = ['[class*="salary"]', '[class*="remun"]'];
    const CLOSE_SELS = ['[class*="clos"]', '[class*="expir"]'];

    const pickText = (root, sels) => {
        for (const s of sels) {
            const el = root.querySelector(s);
            if (el) return (el.textContent || '').trim();
        }
        return '';
    };
    const pickEl = (root, sels) => {
        for (const s of sels) {
            const el = root.querySelector(s);
            if (el) return el;
        }
        return null;
    };

    for (const sel of CONTAINER_SELS) {
        const containers = Array.from(document.querySelectorAll(sel));
        if (containers.length === 0) continue;

        containers.forEach(c => {
            const titleEl = pickEl(c, TITLE_SELS);
            if (!titleEl) return;
            const title = (titleEl.textContent || '').trim();
            if (title.length < 5 || title.length > 200) return;

            const href = titleEl.href || titleEl.getAttribute('href') || '';
            const key = title + '|' + href;
            if (seen.has(key)) return;
            seen.add(key);

            results.push({
                title, href,
                location: pickText(c, LOC_SELS),
                salary:   pickText(c, SAL_SELS),
                closing:  pickText(c, CLOSE_SELS),
            });
        });

        if (results.length > 0) break;
    }
    return results;
}
"""


class GovernmentScraper(BaseScraper):
    """All-state government portal scraper using Playwright.

    Each job produced carries the portal's specific source label (e.g.
    "NSW Government") so the Browse Jobs source filter shows individual states.
    """
    name = "government"
    source_label = "Government Departments"

    def fetch(self, keywords: list[str]) -> list[dict]:
        if not _playwright_available():
            logger.warning(
                "Playwright not installed — government portals scraping disabled. "
                "Run: pip install playwright && python -m playwright install chromium"
            )
            return []
        return self._scrape(keywords, portals=_GOV_PORTALS)

    def _scrape(self, keywords: list[str], portals: list[dict] | None = None) -> list[dict]:
        from playwright.sync_api import sync_playwright

        all_jobs: list[dict] = []
        seen: set[str] = set()
        active_portals = portals or _GOV_PORTALS

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                locale="en-AU",
                timezone_id="Australia/Sydney",
            )
            page = ctx.new_page()

            for portal in active_portals:
                portal_jobs: list[dict] = []
                for kw in keywords[:3]:
                    try:
                        jobs = self._scrape_portal(page, portal, kw, seen)
                        portal_jobs.extend(jobs)
                        logger.info("  %s '%s': %d jobs", portal["name"], kw, len(jobs))
                    except Exception as exc:
                        logger.warning("%s '%s': %s", portal["name"], kw, exc)
                    time.sleep(2)
                all_jobs.extend(portal_jobs)
                if portal_jobs:
                    PORTAL_STATUS[portal["name"]] = "ok"

            browser.close()

        return all_jobs

    def _scrape_portal(self, page, portal: dict, keyword: str, seen: set) -> list[dict]:
        name = portal["name"]
        url = portal["search_url"] + "?" + urlencode(portal["params"](keyword))
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        except Exception as exc:
            PORTAL_STATUS[name] = "error"
            raise RuntimeError(f"{name}: navigation failed — {exc}") from exc

        if response and response.status in (403, 429, 503, 401):
            PORTAL_STATUS[name] = "blocked"
            logger.warning(
                "%s returned HTTP %d — portal may be blocking scrapers. "
                "Use the CSV import fallback to add jobs manually.",
                name, response.status,
            )
            return []

        if response and response.status >= 500:
            PORTAL_STATUS[name] = "error"
            logger.warning("%s returned HTTP %d", name, response.status)
            return []

        wait_sel = portal.get("wait_sel", "article")
        try:
            page.wait_for_selector(wait_sel, timeout=8_000)
        except Exception:
            pass

        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            page.wait_for_timeout(2_000)

        jobs = self._extract_jobs(page, portal, seen)
        if not jobs:
            PORTAL_STATUS[name] = "partial"
        return jobs

    def _extract_jobs(self, page, portal: dict, seen: set) -> list[dict]:
        name = portal["name"]
        base_url = portal["search_url"]
        state = portal.get("state", "")
        try:
            raw: list[dict] = page.evaluate(_EXTRACT_JS)
        except Exception as exc:
            logger.debug("%s DOM eval failed: %s", name, exc)
            return []

        jobs = []
        for item in (raw or []):
            title = item.get("title", "").strip()
            href  = item.get("href", "").strip()
            if not title or not _is_relevant(title):
                continue
            if href and not href.startswith("http"):
                href = urljoin(base_url, href)
            if href in seen:
                continue
            seen.add(href)

            sal_min, sal_max = parse_salary(item.get("salary", ""))
            location = item.get("location") or state or "Australia"
            job = self.make_job(
                title=title,
                organization=name,
                location=location,
                url=href,
                salary_min=sal_min,
                salary_max=sal_max,
                closing_date=item.get("closing", ""),
            )
            # Override source with per-portal label so filters work per state
            job["source"] = name
            if state and not job.get("state"):
                job["state"] = state
            jobs.append(job)
        return jobs


class PortalScraper(GovernmentScraper):
    """Scraper for a single named government portal — used by the coordinator
    to run per-state scrapers individually."""

    def __init__(self, portal_name: str) -> None:
        super().__init__()
        matched = [p for p in _GOV_PORTALS if p["name"] == portal_name]
        if not matched:
            raise ValueError(f"Unknown portal: {portal_name!r}")
        self._portal_def = matched[0]
        self.name = portal_name.lower().replace(" ", "_")
        self.source_label = portal_name

    def fetch(self, keywords: list[str]) -> list[dict]:
        if not _playwright_available():
            logger.warning("Playwright not installed — %s scraping disabled.", self.source_label)
            return []
        return self._scrape(keywords, portals=[self._portal_def])


# ── CSIRO — PageUp portal (server-rendered, no Playwright needed) ─────────────

class CSIROScraper(BaseScraper):
    """CSIRO careers use the PageUp platform (server-rendered HTML)."""
    name = "csiro"
    source_label = "CSIRO"

    _BASE   = "https://jobs.csiro.au"
    _SEARCH = "https://jobs.csiro.au/cw/en/listing/"

    def fetch(self, keywords: list[str]) -> list[dict]:
        all_jobs: list[dict] = []
        seen: set[str] = set()
        try:
            resp = self._get(self._SEARCH)
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("li.lv-item, article.lv-item-container"):
                job = self._parse(item, seen)
                if job:
                    all_jobs.append(job)
        except Exception as exc:
            logger.warning("CSIRO: %s", exc)

        kw_lower = [k.lower() for k in keywords]
        return [j for j in all_jobs if any(k in j["title"].lower() for k in kw_lower)]

    def _parse(self, item, seen: set) -> dict | None:
        a = item.select_one("h3 a, h2 a")
        if not a:
            return None
        title = a.get_text(strip=True)
        href  = a.get("href", "")
        url   = urljoin(self._BASE, href)
        if url in seen or not title:
            return None
        seen.add(url)
        loc_el   = item.select_one("[class*='location'], li:nth-child(2)")
        location = loc_el.get_text(strip=True) if loc_el else "Australia"
        return self.make_job(
            title=title, organization="CSIRO",
            location=location, url=url,
        )
