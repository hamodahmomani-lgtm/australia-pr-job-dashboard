"""
Government portal scrapers — state governments + CSIRO.

All six state portals are JavaScript-rendered SPAs (React/Angular/Vue).
requests.get() returns only the SPA shell; Playwright is required.
CSIRO uses the same PageUp server-rendered portal as the universities and
is left unchanged.
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

_GOV_PORTALS = [
    {
        "name": "NSW Government",
        "search_url": "https://iworkfor.nsw.gov.au/jobs/search",
        "params": lambda kw: {"keyword": kw},
        "wait_sel": "[class*='vacancy'], [class*='job-result'], article",
    },
    {
        "name": "Victoria Careers",
        "search_url": "https://careers.vic.gov.au/jobs",
        "params": lambda kw: {"keyword": kw},
        "wait_sel": "[class*='job-card'], [class*='vacancy-listing']",
    },
    {
        "name": "Queensland Government",
        "search_url": "https://www.workinqueensland.qld.gov.au/en/Find-a-role",
        "params": lambda kw: {"keywords": kw},
        "wait_sel": "[class*='job-item'], [class*='result-item']",
    },
    {
        "name": "SA Government",
        "search_url": "https://www.sagovernmentjobs.sa.gov.au/search",
        "params": lambda kw: {"keywords": kw},
        "wait_sel": "[class*='vacancy'], article",
    },
    {
        "name": "WA Government",
        "search_url": "https://jobs.wa.gov.au/web/Search",
        "params": lambda kw: {"keyword": kw},
        "wait_sel": ".job-item, .search-result, [class*='result']",
    },
    {
        "name": "ACT Government",
        "search_url": "https://www.jobs.act.gov.au/jobs",
        "params": lambda kw: {"keyword": kw},
        "wait_sel": "[class*='job-listing'], [class*='vacancy-item']",
    },
]

_RELEVANT_TERMS = [
    "economist", "economics", "policy", "analyst", "evaluation",
    "research", "data", "intelligence", "lecturer", "statistician",
    "health", "social", "finance", "treasury", "public service",
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
    """State government job portal scraper using Playwright."""
    name = "government"
    source_label = "Government Departments"

    def fetch(self, keywords: list[str]) -> list[dict]:
        if not _playwright_available():
            logger.warning(
                "Playwright not installed — government portals scraping disabled. "
                "Run: pip install playwright && python -m playwright install chromium"
            )
            return []
        return self._scrape(keywords)

    def _scrape(self, keywords: list[str]) -> list[dict]:
        from playwright.sync_api import sync_playwright

        all_jobs: list[dict] = []
        seen: set[str] = set()

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

            for portal in _GOV_PORTALS:
                for kw in keywords[:3]:
                    try:
                        jobs = self._scrape_portal(page, portal, kw, seen)
                        all_jobs.extend(jobs)
                        logger.info(
                            "  %s '%s': %d jobs", portal["name"], kw, len(jobs)
                        )
                    except Exception as exc:
                        logger.warning("%s '%s': %s", portal["name"], kw, exc)
                    time.sleep(2)

            browser.close()

        return all_jobs

    def _scrape_portal(self, page, portal: dict, keyword: str, seen: set) -> list[dict]:
        url = portal["search_url"] + "?" + urlencode(portal["params"](keyword))
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)

        # Try to wait for result elements (gives up quietly if not found)
        wait_sel = portal.get("wait_sel", "article")
        try:
            page.wait_for_selector(wait_sel, timeout=8_000)
        except Exception:
            pass

        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            page.wait_for_timeout(2_000)

        return self._extract_jobs(page, portal["name"], portal["search_url"], seen)

    def _extract_jobs(self, page, org_name: str, base_url: str, seen: set) -> list[dict]:
        try:
            raw: list[dict] = page.evaluate(_EXTRACT_JS)
        except Exception as exc:
            logger.debug("%s DOM eval failed: %s", org_name, exc)
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
            jobs.append(self.make_job(
                title=title,
                organization=org_name,
                location=item.get("location") or "Australia",
                url=href,
                salary_min=sal_min,
                salary_max=sal_max,
                closing_date=item.get("closing", ""),
            ))
        return jobs


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
