"""
APS Jobs scraper — Playwright with network-response interception + shadow-DOM traversal.

APS Jobs is a Salesforce Experience Cloud (Lightning Web Components) site.
Plain requests returns only the SPA shell.  Playwright renders JavaScript,
intercepts the Aura/REST API responses, and also traverses shadow DOM roots
so we extract real job data regardless of component structure.

Install: python -m playwright install chromium
"""

import json
import logging
import re
import time
from urllib.parse import urljoin, quote_plus

from scrapers.base import BaseScraper, parse_salary, parse_date, today

logger = logging.getLogger(__name__)

_APS_BASE   = "https://www.apsjobs.gov.au"
_APS_SEARCH = "https://www.apsjobs.gov.au/s/search"
_MAX_PAGES  = 3


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


# ── Shadow-DOM traversal JS (injected via page.evaluate) ─────────────────────
# Recursively enters every shadow root to find job-card containers.
_EXTRACT_JS = """
() => {
    const results = [];
    const seen = new Set();

    function walkRoot(root) {
        // Descend into shadow roots
        try {
            Array.from(root.querySelectorAll('*')).forEach(el => {
                if (el.shadowRoot) walkRoot(el.shadowRoot);
            });
        } catch(_) {}

        // Container patterns used by Salesforce LWC and generic portals
        const containerSels = [
            '.slds-card', '.slds-card__body',
            '[class*="job-item"]', '[class*="jobItem"]', '[class*="job-card"]',
            '[class*="result-item"]', '[class*="searchResult"]',
            'c-job-item', 'c-position', 'article',
            'li[class*="job"]', 'li[class*="result"]',
        ];

        for (const sel of containerSels) {
            let containers;
            try { containers = Array.from(root.querySelectorAll(sel)); }
            catch(_) { continue; }
            if (containers.length === 0) continue;

            containers.forEach(c => {
                // Title: prefer a link, fall back to heading
                const links  = Array.from(c.querySelectorAll('a[href]'));
                const hdgs   = Array.from(c.querySelectorAll('h1,h2,h3,h4,h5'));
                const titleEl = links[0] || hdgs[0];
                if (!titleEl) return;

                const title = (titleEl.textContent || '').trim();
                if (title.length < 5 || title.length > 200) return;

                const href = (links[0] || {}).href
                          || (links[0] && links[0].getAttribute('href'))
                          || '';
                const key = title + '|' + href;
                if (seen.has(key)) return;
                seen.add(key);

                const pick = (sels) => {
                    for (const s of sels) {
                        const el = c.querySelector(s);
                        if (el) return (el.textContent || '').trim();
                    }
                    return '';
                };

                results.push({
                    title,
                    href,
                    organization: pick(['[class*="agency"]','[class*="depart"]','[class*="org"]']),
                    location:     pick(['[class*="locat"]','[class*="suburb"]','[class*="city"]']),
                    salary:       pick(['[class*="salary"]','[class*="remun"]']),
                    closing:      pick(['[class*="clos"]','[class*="expir"]']),
                });
            });

            if (results.length > 0) break; // found something at this level
        }
    }

    walkRoot(document);
    return results;
}
"""


class APSJobsScraper(BaseScraper):
    name = "aps_jobs"
    source_label = "APS Jobs"

    def fetch(self, keywords: list[str]) -> list[dict]:
        if not _playwright_available():
            logger.warning(
                "Playwright not installed — APS Jobs scraping disabled. "
                "Run: pip install playwright && python -m playwright install chromium"
            )
            return []
        return self._scrape(keywords)

    # ── Main Playwright entry point ───────────────────────────────────────────

    def _scrape(self, keywords: list[str]) -> list[dict]:
        from playwright.sync_api import sync_playwright

        all_jobs: list[dict] = []
        seen_urls: set[str] = set()

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                locale="en-AU",
                timezone_id="Australia/Canberra",
            )
            page = ctx.new_page()
            page.set_extra_http_headers({"Accept-Language": "en-AU,en;q=0.9"})

            for keyword in keywords[:5]:
                try:
                    jobs = self._search_keyword(page, keyword, seen_urls)
                    all_jobs.extend(jobs)
                    logger.info("  APS Jobs '%s': %d jobs", keyword, len(jobs))
                except Exception as exc:
                    logger.warning("APS Jobs error for '%s': %s", keyword, exc)
                time.sleep(3)

            browser.close()

        return all_jobs

    # ── Per-keyword search with pagination ───────────────────────────────────

    def _search_keyword(
        self, page, keyword: str, seen_urls: set
    ) -> list[dict]:
        captured: list[dict] = []

        def _on_response(resp) -> None:
            """Intercept Salesforce Aura / REST API JSON responses."""
            if resp.status != 200:
                return
            ct = resp.headers.get("content-type", "")
            if "json" not in ct:
                return
            url = resp.url
            # Only capture responses that are plausibly job data
            if not any(
                p in url
                for p in ["/aura", "/services/", "apsjobs.gov.au", "search", "job"]
            ):
                return
            try:
                captured.append(resp.json())
            except Exception:
                pass

        page.on("response", _on_response)

        # Navigate to the search page
        page.goto(_APS_SEARCH, wait_until="domcontentloaded", timeout=30_000)
        self._fill_search(page, keyword)

        all_page_jobs: list[dict] = []

        for pg in range(_MAX_PAGES):
            try:
                page.wait_for_load_state("networkidle", timeout=20_000)
            except Exception:
                page.wait_for_timeout(3_000)

            # Try API-response extraction first (most structured)
            if pg == 0 and captured:
                api_jobs = []
                for data in captured:
                    api_jobs.extend(self._from_api_response(data))
                for j in api_jobs:
                    u = j.get("url", "")
                    if u not in seen_urls:
                        seen_urls.add(u)
                        all_page_jobs.append(j)

            # DOM extraction (always attempted — works even when API is empty)
            dom_jobs = self._from_dom(page, seen_urls)
            all_page_jobs.extend(dom_jobs)

            if pg < _MAX_PAGES - 1:
                if not self._click_next(page):
                    break
                time.sleep(1.5)

        page.remove_listener("response", _on_response)
        return all_page_jobs

    # ── Search form interaction ──────────────────────────────────────────────

    def _fill_search(self, page, keyword: str) -> bool:
        selectors = [
            'input[type="search"]',
            'input[placeholder*="keyword" i]',
            'input[name*="keyword" i]',
            'input[placeholder*="search" i]',
            'input[aria-label*="search" i]',
            'lightning-input input',
            '.slds-input',
        ]
        for sel in selectors:
            try:
                el = page.wait_for_selector(sel, timeout=4_000)
                if el and el.is_visible():
                    el.triple_click()
                    el.type(keyword, delay=40)
                    page.keyboard.press("Enter")
                    return True
            except Exception:
                continue
        logger.debug("APS Jobs: could not locate search input for '%s'", keyword)
        return False

    # ── Next-page click ──────────────────────────────────────────────────────

    def _click_next(self, page) -> bool:
        next_sels = [
            'button[title="Next" i]',
            'a[title="Next" i]',
            '[aria-label="Next" i]',
            'button:has-text("Next")',
            'a:has-text("Next")',
            '.pagination-next',
            '[class*="next-page"]',
        ]
        for sel in next_sels:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible() and btn.is_enabled():
                    btn.click()
                    return True
            except Exception:
                continue
        return False

    # ── DOM extraction (shadow-DOM aware) ────────────────────────────────────

    def _from_dom(self, page, seen_urls: set) -> list[dict]:
        try:
            raw: list[dict] = page.evaluate(_EXTRACT_JS)
        except Exception as exc:
            logger.debug("APS Jobs DOM eval failed: %s", exc)
            return []

        jobs = []
        for item in (raw or []):
            title = item.get("title", "").strip()
            href  = item.get("href", "").strip()
            if not title or not href:
                continue
            if href in seen_urls:
                continue
            seen_urls.add(href)

            sal_min, sal_max = parse_salary(item.get("salary", ""))
            jobs.append(self.make_job(
                title=title,
                organization=item.get("organization") or "Australian Public Service",
                location=item.get("location") or "Canberra, ACT",
                url=href,
                salary_min=sal_min,
                salary_max=sal_max,
                closing_date=item.get("closing", ""),
                source="APS Jobs",
            ))
        return jobs

    # ── API-response extraction (Salesforce Aura / generic JSON) ─────────────

    def _from_api_response(self, data: object, depth: int = 0) -> list[dict]:
        """Recursively walk a JSON response looking for job-like objects."""
        if depth > 8:
            return []
        jobs: list[dict] = []
        if isinstance(data, list):
            for item in data:
                jobs.extend(self._from_api_response(item, depth + 1))
        elif isinstance(data, dict):
            # Does this object look like a job posting?
            title_keys = {"title", "jobtitle", "positiontitle", "jobTitle", "Title"}
            if any(k in data for k in title_keys):
                j = self._normalise_api_obj(data)
                if j:
                    return [j]
            # Otherwise recurse into values
            for v in data.values():
                if isinstance(v, (dict, list)):
                    jobs.extend(self._from_api_response(v, depth + 1))
        return jobs

    def _normalise_api_obj(self, obj: dict) -> dict | None:
        title = (
            obj.get("Title") or obj.get("title") or obj.get("jobTitle") or
            obj.get("PositionTitle") or obj.get("Name") or ""
        )
        if not title or len(str(title)) < 4:
            return None

        org = (
            obj.get("Agency") or obj.get("agency") or obj.get("Department") or
            obj.get("organization") or obj.get("Org") or "Australian Public Service"
        )
        loc = (
            obj.get("Location") or obj.get("location") or
            obj.get("Suburb") or obj.get("suburb") or "Canberra, ACT"
        )
        job_id = (
            obj.get("Id") or obj.get("id") or obj.get("jobId") or
            obj.get("RequisitionId") or obj.get("requisitionId") or ""
        )
        url = f"{_APS_BASE}/s/job-details?jobId={job_id}" if job_id else ""

        sal_raw = str(
            obj.get("Salary") or obj.get("salary") or obj.get("SalaryRange") or ""
        )
        sal_min, sal_max = parse_salary(sal_raw)

        return self.make_job(
            title=str(title).strip(),
            organization=str(org).strip(),
            location=str(loc).strip(),
            url=url,
            salary_min=sal_min,
            salary_max=sal_max,
            posted_date=str(
                obj.get("PostedDate") or obj.get("postedDate") or
                obj.get("ListingDate") or ""
            ),
            closing_date=str(
                obj.get("ClosingDate") or obj.get("closingDate") or
                obj.get("ExpiryDate") or ""
            ),
            employment_type=str(obj.get("EmploymentType") or "Full-time"),
        )
