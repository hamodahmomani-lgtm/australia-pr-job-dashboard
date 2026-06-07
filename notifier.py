"""
Telegram notification system.

Uses the Telegram Bot HTTP API directly (no library dependency).
Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env.
"""

import html
import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def _send(text: str, parse_mode: str = "HTML") -> bool:
    """
    Send a message to the configured chat.
    Returns True on success, False on any error (never raises).
    """
    if not _configured():
        logger.debug("Telegram not configured — skipping notification")
        return False
    url = _API_BASE.format(token=TELEGRAM_BOT_TOKEN, method="sendMessage")
    try:
        resp = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": parse_mode},
            timeout=10,
        )
        resp.raise_for_status()
        if not resp.json().get("ok"):
            logger.warning("Telegram API returned not-ok: %s", resp.text[:200])
            return False
        return True
    except Exception as exc:
        logger.warning("Telegram send failed: %s", exc)
        return False


def send_new_jobs_alert(jobs: list[dict]) -> bool:
    """Send a formatted alert for newly discovered jobs."""
    if not jobs:
        return True
    count = len(jobs)
    lines = [f"<b>🇦🇺 {count} new Australian job{'s' if count > 1 else ''} found!</b>\n"]
    for job in jobs[:10]:  # max 10 in one message to stay under 4096-char limit
        sal = ""
        if job.get("salary_min") and job.get("salary_max"):
            sal = f" · <i>${job['salary_min']:,}–${job['salary_max']:,}</i>"
        url = job.get("url") or ""
        title_safe = html.escape(job.get("title", ""))
        org_safe   = html.escape(job.get("organization", ""))
        title_text = f'<a href="{url}">{title_safe}</a>' if url else title_safe
        lines.append(
            f"• {title_text}\n"
            f"  🏢 {org_safe} · 📍 {job.get('location','')}{sal}\n"
            f"  🏷️ {job.get('category','')} · 🌐 {job.get('source','')}"
        )
    if count > 10:
        lines.append(f"\n…and {count - 10} more. Open the dashboard to see all.")
    return _send("\n\n".join(lines))


def send_scrape_summary(summary: dict) -> bool:
    """Send a daily scrape summary."""
    new = summary.get("total_new", 0)
    fetched = summary.get("total_fetched", 0)
    errors = summary.get("errors", [])
    lines = [
        f"<b>🔄 Daily Job Refresh Complete</b>",
        f"New jobs: <b>{new}</b> / Total fetched: {fetched}",
    ]
    per_scraper = summary.get("scrapers", {})
    if per_scraper:
        lines.append("\n<b>Per source:</b>")
        for name, counts in per_scraper.items():
            lines.append(f"  {name}: {counts['new']} new / {counts['total']} total")
    if errors:
        lines.append(f"\n⚠️ Errors ({len(errors)}):")
        for e in errors[:3]:
            lines.append(f"  • {e[:100]}")
    return _send("\n".join(lines))


def send_application_reminder(application: dict) -> bool:
    """Remind about a follow-up due today."""
    title = application.get("title", "a job")
    org = application.get("organization", "")
    follow_up = application.get("follow_up_date", "")
    text = (
        f"⏰ <b>Follow-up reminder</b>\n"
        f"You have a follow-up due for:\n"
        f"<b>{html.escape(title)}</b> at {html.escape(org)}\n"
        f"Status: {application.get('status','')}\n"
        f"Date set: {follow_up}"
    )
    return _send(text)


def send_test_message() -> bool:
    """Send a test ping to verify bot is configured correctly."""
    return _send(
        "✅ <b>Australia PR Job Dashboard</b>\n"
        "Telegram notifications are working correctly."
    )


def is_configured() -> bool:
    return _configured()
