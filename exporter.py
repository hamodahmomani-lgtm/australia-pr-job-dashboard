"""CSV / Excel export for jobs and applications."""

import csv
import io
from datetime import datetime


def jobs_to_csv(jobs: list[dict]) -> bytes:
    """Return jobs as UTF-8-BOM CSV bytes (opens correctly in Excel)."""
    if not jobs:
        return b"\xef\xbb\xbf"  # BOM only

    fields = [
        "id", "title", "organization", "location", "state", "category",
        "source", "salary_min", "salary_max", "employment_type",
        "posted_date", "closing_date", "match_score", "url",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for job in jobs:
        # Format salary as readable string
        row = dict(job)
        writer.writerow(row)

    return ("\xef\xbb\xbf" + buf.getvalue()).encode("utf-8")


def applications_to_csv(applications: list[dict]) -> bytes:
    """Return applications as UTF-8-BOM CSV bytes."""
    if not applications:
        return b"\xef\xbb\xbf"

    fields = [
        "id", "title", "organization", "category",
        "status", "applied_date", "follow_up_date",
        "response_date", "notes", "salary_min", "salary_max",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for app in applications:
        writer.writerow({f: app.get(f, "") for f in fields})

    return ("\xef\xbb\xbf" + buf.getvalue()).encode("utf-8")


def export_filename(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{prefix}_{ts}.csv"
