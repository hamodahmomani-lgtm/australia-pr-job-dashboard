# 🇦🇺 Australia PR Job Dashboard

A Streamlit dashboard for tracking Australian job opportunities relevant to skilled-migration Permanent Residency, with CV matching, application tracking, and cover letter generation calibrated to government policy, economics, and evaluation roles.

## Features

| Feature | Description |
|---|---|
| **Job Database** | 30+ pre-loaded jobs across 13 categories; live scraping from 14 sources |
| **State Government Coverage** | All 8 states/territories: NSW, VIC, QLD, SA, WA, ACT, TAS, NT |
| **CV Matching Engine** | TF-IDF + domain keyword scoring ranked against your CV |
| **Skills Gap Analysis** | Per-job breakdown of matched/missing skills with tailoring tips |
| **Application Tracker** | Pipeline: Bookmarked → Applied → Interview → Offer |
| **Cover Letter Generator** | 12 category-specific templates — including state gov roles |
| **CSV Import Fallback** | Manual import when a portal blocks automated scraping |
| **PR Relevance Flags** | ANZSCO codes and MLTSSL eligibility per job category |
| **Portal Smoke Test** | `smoke_test.py` audits every state portal — Working / Blocked / Error |

---

## Job Categories

| Category | ANZSCO | MLTSSL |
|---|---|---|
| Health Economist | 224111 | ✅ |
| Economist | 224411 | ✅ |
| Research Fellow | 210299 | ✅ |
| Lecturer | 242111 | ✅ |
| Government Research Officer | 224411 | ✅ |
| Health Policy Officer | 224111 | ✅ |
| Policy Analyst | 224212 | — |
| Senior Policy Officer | 224212 | — |
| Evaluation Specialist | 224212 | — |
| Program Evaluation Officer | 224212 | — |
| Data Analyst | 261111 | — |
| Business Intelligence Analyst | 261111 | — |
| Tutor | 249299 | ✗ |

---

## State Government Coverage

| State/Territory | Portal | Source Label | Notes |
|---|---|---|---|
| NSW | iworkfor.nsw.gov.au | NSW Government | SPA — Playwright required |
| VIC | careers.vic.gov.au | Victoria Government | SPA — Playwright required |
| QLD | workinqueensland.qld.gov.au | Queensland Government | SPA — Playwright required |
| SA | sagovernmentjobs.sa.gov.au | SA Government | SPA — Playwright required |
| WA | jobs.wa.gov.au | WA Government | SPA — Playwright required |
| ACT | jobs.act.gov.au | ACT Government | SPA — Playwright required |
| TAS | jobs.tas.gov.au | Tasmania Government | SPA — Playwright required |
| NT | jobs.nt.gov.au | NT Government | SPA — Playwright required |

If a portal blocks scraping, use **Settings → CSV Import** to add jobs manually.

---

## Job Sources

- APS Jobs (Australian Public Service — Salesforce LWC portal)
- University Portals (19 universities via PageUp)
- CSIRO (PageUp)
- Seek
- Consulting Firms (Deloitte, KPMG, PwC, EY)
- All 8 state/territory government portals

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/hamodahmomani-lgtm/australia-pr-job-dashboard.git
cd australia-pr-job-dashboard
```

### 2. Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright (for state government portals)

```bash
python -m playwright install chromium
```

### 5. Run the dashboard

```bash
streamlit run app.py
```

The dashboard opens at **http://localhost:8501**.

---

## Testing — Smoke Test

Run the portal smoke test before scraping to check which state portals are accessible:

```bash
# Quick HTTP check (no Playwright, ~30 seconds)
python smoke_test.py

# Full Playwright extraction test (~5 minutes, requires Playwright)
python smoke_test.py --full

# Test a single state
python smoke_test.py --portal NSW
python smoke_test.py --portal Tasmania

# List all known portals
python smoke_test.py --list
```

### Example output

```
🇦🇺  Australia PR Job Dashboard — Portal Smoke Test
Time: 2026-06-07 14:22:01
Mode: HTTP-only (quick)
Portals: 8

Portal                      State       Status     HTTP     ms  Notes
──────────────────────────────────────────────────────────────────────
NSW Government              NSW         WORKING      200   312ms
Victoria Government         VIC         WORKING      200   445ms
Queensland Government       QLD         PARTIAL      200   890ms  0 jobs
SA Government               SA          WORKING      200   520ms
WA Government               WA          BLOCKED      403   180ms  HTTP 403 — portal blocking
ACT Government              ACT         WORKING      200   340ms
Tasmania Government         TAS         WORKING      200   610ms
NT Government               NT          WORKING      200   750ms

Blocked / erroring portals — use CSV import as fallback:
  • WA Government (WA): HTTP 403 — portal is actively blocking scrapers
    → Then: use Settings → CSV Import to manually add jobs
```

### Exit codes

| Code | Meaning |
|---|---|
| 0 | All portals are accessible |
| 1 | One or more portals are blocked or erroring |

---

## CSV Import Fallback

When a portal blocks scraping (403/429 response), use the manual CSV import:

1. Go to **⚙️ Settings → CSV Import**
2. Click **Download CSV template** to get the correct format
3. Fill in jobs from the portal website manually
4. Upload or paste the CSV and choose the source state
5. Click **Import jobs from CSV**

### CSV format

```csv
title,organization,location,url,salary_min,salary_max,description,requirements,posted_date,closing_date,employment_type,source
Senior Policy Officer,WA Government,Perth WA,https://jobs.wa.gov.au/...,95000,115000,Description here,Requirements here,,,Ongoing Full-time,WA Government
```

---

## Project Structure

```
australia-pr-job-dashboard/
├── app.py                  # Main Streamlit dashboard (6 pages + 4 tabs in Settings)
├── config.py               # Categories, sources, keywords, APS classifications
├── database.py             # SQLite layer — init, CRUD for all tables
├── jobs.py                 # Sample job data seeding
├── cv_match.py             # TF-IDF matching engine, skills-gap analysis, PR scores
├── cover_letter.py         # Cover letter templates (12 categories)
├── cv_parser.py            # PDF/DOCX/TXT parsing
├── exporter.py             # CSV export utilities
├── notifier.py             # Telegram bot integration
├── scheduler.py            # APScheduler for background scraping
├── smoke_test.py           # Portal smoke test script
├── requirements.txt        # Python dependencies
└── scrapers/
    ├── __init__.py
    ├── base.py             # BaseScraper, rate limiting, normalisation
    ├── coordinator.py      # Multi-threaded orchestration + per-state runner
    ├── aps_jobs.py         # APS Jobs (Playwright + shadow DOM)
    ├── pageup.py           # University portals (PageUp platform)
    ├── government.py       # All 8 state/territory gov portals (Playwright)
    ├── seek.py             # Seek.com.au API
    ├── consulting.py       # Deloitte, KPMG, PwC, EY
    └── import_csv.py       # CSV / manual import fallback
```

---

## Database Tables

| Table | Contents |
|---|---|
| `jobs` | Job listings with category, state, source, salary, description, URL |
| `applications` | Applications with status pipeline and notes |
| `user_profile` | CV text, skills, education, visa status |
| `cover_letters` | Saved cover letters with version history |
| `scrape_log` | Per-scrape run summaries |

---

## Usage Guide

### Setting Up Your Profile
1. Go to **⚙️ Settings → Profile**
2. Enter your name, email, phone, LinkedIn URL
3. Select your visa status and target roles
4. Paste your full CV text → used for all job matching

### Browsing Jobs
1. Go to **🔍 Browse Jobs**
2. Filter by **Category**, **Source** (including per-state), **State**, keyword, or salary
3. Each job shows a **match score** if your CV is saved
4. Click **Details & Actions** to see skills gap and tailoring suggestions
5. Bookmark or mark as applied from the card

### Running Individual State Scrapers
1. Go to **⚙️ Settings → Scrapers & Schedule**
2. Select a state scraper (e.g. `tasmania_government`)
3. Click **Run now**

### Importing Jobs Manually
1. Go to **⚙️ Settings → CSV Import**
2. Download the template, fill in jobs from the portal
3. Upload and import

### Tracking Applications
1. Go to **📋 Applications**
2. Update status, add notes, set follow-up dates

### Generating Cover Letters
1. Go to **✍️ Cover Letters**
2. Select a job and optionally enter the hiring manager's name
3. Click **Generate Cover Letter**
4. Edit and download

---

## Extending the Scrapers

Each government portal uses `PortalScraper` (a thin Playwright wrapper). To add a new portal:

```python
# In scrapers/government.py, add to _GOV_PORTALS:
{
    "name": "New Government",
    "state": "XX",
    "search_url": "https://jobs.example.gov.au/search",
    "params": lambda kw: {"keyword": kw},
    "wait_sel": "article, [class*='job']",
}
```

Then add `"New Government"` to `JOB_SOURCES` in `config.py` and `STATE_GOV_SOURCES`.

---

## PR / Visa Context

The dashboard is designed around the **Australian Skilled Migration** pathway:
- MLTSSL-eligible jobs (Health Economist, Economist, Research Fellow, Lecturer) receive a +5 score boost
- Target government policy/evaluation role titles receive a +3 score boost
- `is_pr_relevant = 1` tags jobs aligned with ANZSCO skilled occupations
- Prioritises **ongoing** APS and state government positions for points-test claims

---

## Requirements

- Python 3.11+
- Playwright with Chromium (for state government portals): `python -m playwright install chromium`
- See `requirements.txt` for Python package versions

No API keys required for sample data. Seek uses the public Chalice Search API (no key needed).

---

## Contributing

Pull requests welcome. Please open an issue first for significant changes.

## License

MIT
