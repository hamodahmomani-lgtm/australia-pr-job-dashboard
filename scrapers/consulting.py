"""
Consulting firm scrapers — Deloitte AU, KPMG AU, PwC AU, EY AU.

All four firms use Workday or Taleo ATS platforms that render job listings
via JavaScript.  Plain requests returns only the SPA shell.  Each scraper
launches a headless Chromium browser via Playwright, waits for networkidle,
then extracts jobs from the rendered DOM using broad container selectors
that work across different ATS implementations.

Install: python -m playwright install chromium
"""

import logging
import time
from urllib.parse import urljoin, urlencode

from scrapers.base import BaseScraper, parse_salary

logger = logging.getLogger(__name__)


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


# ── Generic DOM-extraction JS ─────────────────────────────────────────────────
# Tries a ranked list of container selectors; returns first set that yields ≥1 job.

_EXTRACT_JS = """
() => {
    const results = [];
    const seen = new Set();

    const CONTAINER_SELS = [
        'li[class*="result"]', 'li[class*="job"]', 'li[class*="position"]',
        'li[class*="posting"]', 'li[class*="vacancy"]',
        'article', 'div[class*="job-result"]', 'div[class*="job-card"]',
        'div[class*="position"]', 'div[class*="vacancy"]',
        '[class*="opportunity"]', 'tr[class*="job"]', 'tr[class*="result"]',
    ];
    const TITLE_SELS = [
        'h2 a', 'h3 a', 'h4 a',
        'a[class*="title"]', 'a[class*="job"]', 'a[class*="position"]',
        '[class*="title"] a', 'a[href]',
    ];
    const LOC_SELS   = ['[class*="locat"]', '[class*="city"]', '[class*="office"]'];
    const SAL_SELS   = ['[class*="salary"]', '[class*="remun"]'];

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
            });
        });

        if (results.length > 0) break;
    }
    return results;
}
"""


# ── Shared Playwright base class ──────────────────────────────────────────────

class _PlaywrightFirmScraper(BaseScraper):
    source_label = "Consulting Firms"

    _SEARCH_URL: str = ""
    _ORG: str = ""
    _KEYWORD_PARAM: str = "q"
    _EXTRA_PARAMS: dict = {}
    _MAX_KW: int = 3

    def fetch(self, keywords: list[str]) -> list[dict]:
        if not _playwright_available():
            logger.warning(
                "Playwright not installed — %s scraping disabled. "
                "Run: pip install playwright && python -m playwright install chromium",
                self._ORG,
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
            )
            page = ctx.new_page()

            for kw in keywords[:self._MAX_KW]:
                try:
                    jobs = self._search_kw(page, kw, seen)
                    all_jobs.extend(jobs)
                    logger.info("  %s '%s': %d jobs", self._ORG, kw, len(jobs))
                except Exception as exc:
                    logger.warning("%s '%s': %s", self._ORG, kw, exc)
                time.sleep(3)

            browser.close()

        return all_jobs

    def _search_kw(self, page, keyword: str, seen: set) -> list[dict]:
        params = {self._KEYWORD_PARAM: keyword, **self._EXTRA_PARAMS}
        url = self._SEARCH_URL + "?" + urlencode(params)
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        try:
            page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            page.wait_for_timeout(3_000)
        return self._extract(page, seen)

    def _extract(self, page, seen: set) -> list[dict]:
        try:
            raw: list[dict] = page.evaluate(_EXTRACT_JS)
        except Exception as exc:
            logger.debug("%s DOM eval failed: %s", self._ORG, exc)
            return []

        jobs = []
        for item in (raw or []):
            title = item.get("title", "").strip()
            href  = item.get("href", "").strip()
            if not title or not href:
                continue
            if not href.startswith("http"):
                href = urljoin(self._SEARCH_URL, href)
            if href in seen:
                continue
            seen.add(href)

            sal_min, sal_max = parse_salary(item.get("salary", ""))
            jobs.append(self.make_job(
                title=title,
                organization=self._ORG,
                location=item.get("location") or "Australia",
                url=href,
                salary_min=sal_min,
                salary_max=sal_max,
            ))
        return jobs


# ── Firm-specific subclasses ──────────────────────────────────────────────────

class DeloitteScraper(_PlaywrightFirmScraper):
    name = "deloitte"
    _SEARCH_URL   = "https://apply.deloitte.com/careers/SearchJobs"
    _ORG          = "Deloitte Access Economics"
    _KEYWORD_PARAM = "Keywords"
    _EXTRA_PARAMS = {"Country": "AU"}


class KPMGScraper(_PlaywrightFirmScraper):
    name = "kpmg"
    _SEARCH_URL   = "https://kpmg.recruitmenthub.com.au/Vacancy/VacancyList"
    _ORG          = "KPMG Australia"
    _KEYWORD_PARAM = "keywords"


class PwCScraper(_PlaywrightFirmScraper):
    name = "pwc"
    _SEARCH_URL   = "https://www.pwc.com.au/careers/search-jobs.html"
    _ORG          = "PwC Australia"
    _KEYWORD_PARAM = "q"
    _EXTRA_PARAMS = {"country": "AU"}


class EYScraper(_PlaywrightFirmScraper):
    name = "ey"
    _SEARCH_URL   = "https://careers.ey.com/ey/search/"
    _ORG          = "EY Australia"
    _KEYWORD_PARAM = "q"
    _EXTRA_PARAMS = {"country": "Australia"}


ALL_CONSULTING_SCRAPERS = [DeloitteScraper, KPMGScraper, PwCScraper, EYScraper]
