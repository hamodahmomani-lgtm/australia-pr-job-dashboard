"""Base scraper — shared session, retry logic, rate limiting, normalisation."""

import time
import logging
import re
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import REQUEST_DELAY, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# Rotate through realistic User-Agent strings
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]
_UA_INDEX = 0


def _next_ua() -> str:
    global _UA_INDEX
    ua = _USER_AGENTS[_UA_INDEX % len(_USER_AGENTS)]
    _UA_INDEX += 1
    return ua


def make_session() -> requests.Session:
    """Return a requests.Session with retry logic and realistic headers."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": _next_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    })
    return session


# ── Date helpers ──────────────────────────────────────────────────────────────

def today(offset: int = 0) -> str:
    return (datetime.today() + timedelta(days=offset)).strftime("%Y-%m-%d")


def parse_date(raw: str) -> str:
    """Best-effort date parser — returns YYYY-MM-DD or today() on failure."""
    if not raw:
        return today()
    raw = raw.strip()
    formats = [
        "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d", "%d/%m/%Y", "%d %B %Y", "%d %b %Y",
        "%B %d, %Y", "%b %d, %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    # Try to extract YYYY-MM-DD with regex
    m = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return m.group(1)
    return today()


# ── Salary helpers ────────────────────────────────────────────────────────────

def parse_salary(raw: str) -> tuple[int, int]:
    """Extract (min, max) from a salary string like '$95,000 – $110,000'."""
    if not raw:
        return 0, 0
    numbers = re.findall(r"\d[\d,]*", raw)
    nums = [int(n.replace(",", "")) for n in numbers if len(n.replace(",", "")) >= 4]
    if len(nums) >= 2:
        return min(nums[:2]), max(nums[:2])
    if len(nums) == 1:
        return nums[0], nums[0]
    return 0, 0


# ── State inference ───────────────────────────────────────────────────────────

_STATE_PATTERNS = {
    "ACT": ["act", "canberra", "australian capital territory"],
    "NSW": ["nsw", "new south wales", "sydney", "newcastle", "wollongong"],
    "VIC": ["vic", "victoria", "melbourne", "geelong", "ballarat"],
    "QLD": ["qld", "queensland", "brisbane", "gold coast", "sunshine coast"],
    "SA":  ["sa", "south australia", "adelaide"],
    "WA":  ["wa", "western australia", "perth"],
    "TAS": ["tas", "tasmania", "hobart", "launceston"],
    "NT":  ["nt", "northern territory", "darwin"],
}


def infer_state(location: str) -> str:
    loc = location.lower()
    for state, patterns in _STATE_PATTERNS.items():
        if any(p in loc for p in patterns):
            return state
    return "Remote"


# ── Category inference ────────────────────────────────────────────────────────

def infer_category(title: str, description: str) -> str:
    from config import CATEGORY_KEYWORDS
    text = f"{title} {description}".lower()
    best, best_score = "Economist", 0
    for cat, kws in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in kws if kw.lower() in text)
        if score > best_score:
            best_score = score
            best = cat
    return best


# ── Base class ────────────────────────────────────────────────────────────────

class BaseScraper(ABC):
    name: str = "base"
    source_label: str = "Unknown"

    def __init__(self) -> None:
        self.session = make_session()
        self._last_request = 0.0

    def _get(self, url: str, **kwargs) -> requests.Response:
        """Rate-limited GET with automatic header rotation."""
        elapsed = time.time() - self._last_request
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self.session.headers["User-Agent"] = _next_ua()
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT, **kwargs)
        self._last_request = time.time()
        resp.raise_for_status()
        return resp

    def _post(self, url: str, **kwargs) -> requests.Response:
        elapsed = time.time() - self._last_request
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self.session.headers["User-Agent"] = _next_ua()
        resp = self.session.post(url, timeout=REQUEST_TIMEOUT, **kwargs)
        self._last_request = time.time()
        resp.raise_for_status()
        return resp

    @abstractmethod
    def fetch(self, keywords: list[str]) -> list[dict]:
        """Return a list of normalised job dicts."""
        ...

    def run(self, keywords: list[str]) -> list[dict]:
        """Public entry point — catches all exceptions, logs them."""
        try:
            jobs = self.fetch(keywords)
            logger.info("%s returned %d jobs", self.name, len(jobs))
            return jobs
        except Exception as exc:
            logger.error("%s failed: %s", self.name, exc, exc_info=True)
            return []

    # ── Job dict factory ──────────────────────────────────────────────────────

    def make_job(
        self,
        title: str,
        organization: str,
        location: str = "",
        description: str = "",
        requirements: str = "",
        url: str = "",
        posted_date: str = "",
        closing_date: str = "",
        salary_min: int = 0,
        salary_max: int = 0,
        employment_type: str = "Full-time",
        category: str = "",
        **_extra,
    ) -> dict:
        state = infer_state(location)
        cat = category or infer_category(title, description)
        return {
            "title": title.strip(),
            "organization": organization.strip(),
            "location": location.strip(),
            "state": state,
            "category": cat,
            "source": self.source_label,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "description": description.strip(),
            "requirements": requirements.strip(),
            "url": url.strip(),
            "posted_date": parse_date(posted_date) if posted_date else today(),
            "closing_date": parse_date(closing_date) if closing_date else today(21),
            "employment_type": employment_type,
            "is_pr_relevant": 1,
        }
