#!/usr/bin/env python3
"""
Smoke test for Australian state/territory government job portals.

Audits each portal and reports: Working | Partial | Blocked | Error | Unknown.

Usage:
    python smoke_test.py                # quick HTTP-only test (default)
    python smoke_test.py --full         # also attempt Playwright job extraction
    python smoke_test.py --portal NSW   # test a single named portal
    python smoke_test.py --list         # list all known portals

Exit codes:
    0  all portals returned at least a 2xx/3xx response
    1  one or more portals are blocked or erroring
"""

import argparse
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime

# ── Colours (ANSI) ────────────────────────────────────────────────────────────

_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_CYAN   = "\033[96m"
_RESET  = "\033[0m"
_BOLD   = "\033[1m"


def _col(text: str, colour: str) -> str:
    return f"{colour}{text}{_RESET}"


# ── Portal registry ───────────────────────────────────────────────────────────

@dataclass
class Portal:
    name: str
    state: str
    url: str
    search_param: str
    test_keyword: str = "policy analyst"
    status: str = "unknown"
    http_code: int = 0
    jobs_found: int = 0
    error: str = ""
    latency_ms: int = 0


PORTALS: list[Portal] = [
    Portal("NSW Government",        "NSW", "https://iworkfor.nsw.gov.au/jobs/search",                  "keyword"),
    Portal("Victoria Government",   "VIC", "https://careers.vic.gov.au/jobs",                          "keyword"),
    Portal("Queensland Government", "QLD", "https://www.workinqueensland.qld.gov.au/en/Find-a-role",   "keywords"),
    Portal("SA Government",         "SA",  "https://www.sagovernmentjobs.sa.gov.au/search",             "keywords"),
    Portal("WA Government",         "WA",  "https://jobs.wa.gov.au/web/Search",                         "keyword"),
    Portal("ACT Government",        "ACT", "https://www.jobs.act.gov.au/jobs",                          "keyword"),
    Portal("Tasmania Government",   "TAS", "https://jobs.tas.gov.au/search",                            "keyword"),
    Portal("NT Government",         "NT",  "https://jobs.nt.gov.au/search",                             "Keywords"),
]

# APS Jobs (different platform)
PORTALS_EXTRA: list[Portal] = [
    Portal("APS Jobs",     "ACT/National", "https://www.apsjobs.gov.au/s/",  "keyword"),
]


def _http_check(portal: Portal, timeout: int = 15) -> None:
    """Quick HTTP GET to the portal's search URL with a test keyword."""
    from urllib.parse import urlencode
    kw_enc = urlencode({portal.search_param: portal.test_keyword})
    full_url = f"{portal.url}?{kw_enc}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
    }
    req = urllib.request.Request(full_url, headers=headers)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            portal.http_code = resp.status
            portal.latency_ms = int((time.monotonic() - t0) * 1000)
            if resp.status < 400:
                portal.status = "ok"
            else:
                portal.status = "blocked"
    except urllib.error.HTTPError as exc:
        portal.http_code = exc.code
        portal.latency_ms = int((time.monotonic() - t0) * 1000)
        if exc.code in (403, 401, 429):
            portal.status = "blocked"
            portal.error = f"HTTP {exc.code} — portal is actively blocking scrapers"
        elif exc.code >= 500:
            portal.status = "error"
            portal.error = f"HTTP {exc.code} — server error"
        else:
            portal.status = "partial"
            portal.error = f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        portal.latency_ms = int((time.monotonic() - t0) * 1000)
        portal.status = "error"
        portal.error = str(exc.reason)
    except Exception as exc:
        portal.latency_ms = int((time.monotonic() - t0) * 1000)
        portal.status = "error"
        portal.error = str(exc)


def _playwright_check(portal: Portal, keywords: list[str]) -> None:
    """Full Playwright extraction for this specific portal only."""
    try:
        from scrapers.government import _GOV_PORTALS, PortalScraper, PORTAL_STATUS
    except ImportError:
        portal.error = "scrapers.government not importable"
        return

    if portal.name not in {p["name"] for p in _GOV_PORTALS}:
        portal.error = f"Portal '{portal.name}' not in _GOV_PORTALS"
        return

    try:
        # PortalScraper targets only this portal so --portal NSW doesn't
        # trigger all eight portals as GovernmentScraper.run() would.
        scraper = PortalScraper(portal.name)
        jobs = scraper.run(keywords[:4])
        portal.jobs_found = len(jobs)
        portal.status = PORTAL_STATUS.get(portal.name, portal.status)
    except Exception as exc:
        portal.status = "error"
        portal.error = str(exc)


def _status_badge(status: str) -> str:
    if status == "ok":
        return _col("WORKING  ", _GREEN)
    if status == "partial":
        return _col("PARTIAL  ", _YELLOW)
    if status == "blocked":
        return _col("BLOCKED  ", _RED)
    if status == "error":
        return _col("ERROR    ", _RED)
    return _col("UNKNOWN  ", _CYAN)


def _print_table(portals: list[Portal]) -> None:
    width = 26
    print()
    print(_col(f"{'Portal':<{width}}  {'State':<10}  {'Status'}     {'HTTP':>4}  {'ms':>5}  Notes", _BOLD))
    print("─" * 90)
    for p in portals:
        badge = _status_badge(p.status)
        http  = str(p.http_code) if p.http_code else "—"
        ms    = str(p.latency_ms) if p.latency_ms else "—"
        note  = p.error or (f"{p.jobs_found} job(s)" if p.jobs_found else "")
        print(f"{p.name:<{width}}  {p.state:<10}  {badge}  {http:>4}  {ms:>5}ms  {note}")
    print()


def _print_recommendations(portals: list[Portal]) -> None:
    blocked = [p for p in portals if p.status in ("blocked", "error")]
    if not blocked:
        print(_col("All portals are accessible.", _GREEN))
        return
    print(_col("Blocked / erroring portals — use CSV import as fallback:", _YELLOW))
    for p in blocked:
        print(f"  • {p.name} ({p.state}): {p.error or p.status}")
        print(f"    → Run:  python smoke_test.py --portal '{p.name}'  to re-check")
        print(f"    → Then: use Settings → CSV Import to manually add jobs")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test Australian government job portals.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Use Playwright to attempt actual job extraction (slower; requires Playwright installed)",
    )
    parser.add_argument(
        "--portal", metavar="NAME",
        help="Test only this named portal (partial match, case-insensitive)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List all known portals and exit",
    )
    parser.add_argument(
        "--timeout", type=int, default=15,
        help="HTTP timeout in seconds (default: 15)",
    )
    args = parser.parse_args()

    all_portals = PORTALS + PORTALS_EXTRA

    if args.list:
        for p in all_portals:
            print(f"  {p.state:<10}  {p.name}")
        return 0

    target = all_portals
    if args.portal:
        q = args.portal.lower()
        target = [p for p in all_portals if q in p.name.lower() or q in p.state.lower()]
        if not target:
            print(f"No portal matched '{args.portal}'. Run with --list to see names.")
            return 1

    print(_col(f"\n🇦🇺  Australia PR Job Dashboard — Portal Smoke Test", _BOLD))
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'Playwright (full)' if args.full else 'HTTP-only (quick)'}")
    print(f"Portals: {len(target)}\n")

    for p in target:
        print(f"  Checking {p.name}…", end=" ", flush=True)
        _http_check(p, timeout=args.timeout)
        print(_status_badge(p.status), f"({p.latency_ms}ms)")
        time.sleep(1)

    if args.full:
        print("\nRunning Playwright extraction (this may take a few minutes)…")
        kws = ["policy analyst", "health economist", "evaluation officer"]
        for p in target:
            if p.name in {pp.name for pp in PORTALS}:
                print(f"  Extracting {p.name}…")
                _playwright_check(p, kws)

    _print_table(target)
    _print_recommendations(target)

    # Audit summary
    ok      = sum(1 for p in target if p.status == "ok")
    partial = sum(1 for p in target if p.status == "partial")
    blocked = sum(1 for p in target if p.status == "blocked")
    errors  = sum(1 for p in target if p.status == "error")
    unknown = sum(1 for p in target if p.status == "unknown")

    print("Audit summary:")
    print(f"  {_col(f'{ok} Working', _GREEN)}")
    print(f"  {_col(f'{partial} Partial', _YELLOW)}")
    print(f"  {_col(f'{blocked} Blocked', _RED)}")
    print(f"  {_col(f'{errors} Error', _RED)}")
    if unknown:
        print(f"  {_col(f'{unknown} Unknown', _CYAN)}")
    print()

    return 0 if (blocked + errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
