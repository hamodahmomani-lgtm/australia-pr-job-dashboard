"""
CSV / manual import fallback for government job portals.

Use this when a state portal blocks automated scraping.  Export job
listings from the portal manually (most portals let you copy details)
and paste them into a CSV that matches the template below.

Template columns (order matters for headerless files, but header row is preferred):
    title, organization, location, url, salary_min, salary_max,
    description, requirements, posted_date, closing_date, employment_type, source

Usage (CLI):
    python -c "from scrapers.import_csv import get_csv_template; print(get_csv_template())"

Usage (Python):
    from scrapers.import_csv import load_jobs_from_csv
    with open("my_jobs.csv") as f:
        jobs = load_jobs_from_csv(f.read(), source="Tasmania Government")
"""

import csv
import io
import logging
from scrapers.base import BaseScraper, parse_date, parse_salary, today, infer_state, infer_category

logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    "title", "organization", "location", "url",
    "salary_min", "salary_max", "description", "requirements",
    "posted_date", "closing_date", "employment_type", "source",
]

CSV_TEMPLATE_ROWS = [
    CSV_COLUMNS,
    [
        "Senior Policy Officer",
        "NSW Government",
        "Sydney NSW",
        "https://iworkfor.nsw.gov.au/jobs/12345",
        "95000", "115000",
        "Lead policy development and analysis for the department.",
        "PhD or Masters in economics, policy, or related field.",
        "", "", "Ongoing Full-time", "NSW Government",
    ],
    [
        "Health Policy Officer",
        "Department of Health SA",
        "Adelaide SA",
        "https://www.sagovernmentjobs.sa.gov.au/jobs/67890",
        "85000", "100000",
        "Develop and review health policy frameworks for SA Health.",
        "Degree in health policy, public health, or economics.",
        "", "", "Ongoing Full-time", "SA Government",
    ],
    [
        "Program Evaluation Officer",
        "Victorian Department of Health",
        "Melbourne VIC",
        "https://careers.vic.gov.au/jobs/11223",
        "90000", "110000",
        "Design and implement program evaluations for community health programs.",
        "Experience in quantitative evaluation methods; Stata or R skills.",
        "", "", "Fixed Term", "Victoria Government",
    ],
]


def get_csv_template() -> str:
    """Return a CSV template string with example rows for manual data entry."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in CSV_TEMPLATE_ROWS:
        writer.writerow(row)
    return buf.getvalue()


def load_jobs_from_csv(csv_text: str, source: str = "Manual Import") -> list[dict]:
    """
    Parse CSV text into job dicts compatible with database.save_job().

    Accepts both headerless (column-order) and header-row CSV files.
    Missing fields default to sensible values.  Returns empty list on
    parse error (logs warning; does not raise).
    """
    if not csv_text or not csv_text.strip():
        return []

    try:
        reader = csv.reader(io.StringIO(csv_text.strip()))
        rows = list(reader)
    except Exception as exc:
        logger.warning("CSV parse error: %s", exc)
        return []

    if not rows:
        return []

    header = [c.lower().strip() for c in rows[0]]
    has_header = "title" in header

    if has_header:
        data_rows = rows[1:]
        col_map = {col: idx for idx, col in enumerate(header)}
    else:
        data_rows = rows
        col_map = {col: idx for idx, col in enumerate(CSV_COLUMNS)}

    def _get(row: list[str], col: str, default: str = "") -> str:
        idx = col_map.get(col)
        if idx is None or idx >= len(row):
            return default
        return row[idx].strip()

    jobs: list[dict] = []
    for i, row in enumerate(data_rows):
        if not row or not any(row):
            continue
        title = _get(row, "title")
        if not title:
            logger.debug("CSV row %d: missing title — skipped", i + 2)
            continue

        org = _get(row, "organization") or source
        location = _get(row, "location") or "Australia"
        url = _get(row, "url")
        state = infer_state(location)

        sal_raw_min = _get(row, "salary_min", "0")
        sal_raw_max = _get(row, "salary_max", "0")
        try:
            sal_min = int(float(sal_raw_min.replace(",", "").replace("$", "") or "0"))
            sal_max = int(float(sal_raw_max.replace(",", "").replace("$", "") or "0"))
        except (ValueError, TypeError):
            sal_min = sal_max = 0

        description  = _get(row, "description")
        requirements = _get(row, "requirements")
        row_source   = _get(row, "source") or source

        posted_raw  = _get(row, "posted_date")
        closing_raw = _get(row, "closing_date")

        cat = infer_category(title, description)
        emp_type = _get(row, "employment_type") or "Full-time"

        jobs.append({
            "title":           title,
            "organization":    org,
            "location":        location,
            "state":           state,
            "category":        cat,
            "source":          row_source,
            "salary_min":      sal_min,
            "salary_max":      sal_max,
            "description":     description,
            "requirements":    requirements,
            "url":             url,
            "posted_date":     parse_date(posted_raw) if posted_raw else today(),
            "closing_date":    parse_date(closing_raw) if closing_raw else today(21),
            "employment_type": emp_type,
            "is_pr_relevant":  1,
        })

    logger.info("CSV import: parsed %d valid job(s) from %d row(s)", len(jobs), len(data_rows))
    return jobs


class CSVImportScraper(BaseScraper):
    """
    Pseudo-scraper that loads jobs from a local CSV file path.

    Designed as a fallback when a government portal cannot be scraped.
    Set CSV_IMPORT_PATH environment variable or pass csv_path to __init__.
    """
    name = "csv_import"
    source_label = "Manual Import"

    def __init__(self, csv_path: str = "", source: str = "") -> None:
        super().__init__()
        import os
        self._csv_path = csv_path or os.getenv("CSV_IMPORT_PATH", "")
        if source:
            self.source_label = source

    def fetch(self, keywords: list[str]) -> list[dict]:
        if not self._csv_path:
            logger.debug("CSVImportScraper: no csv_path configured — nothing to import")
            return []
        try:
            with open(self._csv_path, encoding="utf-8") as f:
                csv_text = f.read()
        except OSError as exc:
            logger.warning("CSVImportScraper: cannot read %s — %s", self._csv_path, exc)
            return []

        jobs = load_jobs_from_csv(csv_text, source=self.source_label)

        kw_lower = [k.lower() for k in keywords]
        if kw_lower:
            jobs = [
                j for j in jobs
                if any(
                    k in (j.get("title", "") + " " + j.get("description", "")).lower()
                    for k in kw_lower
                )
            ]
        return jobs
