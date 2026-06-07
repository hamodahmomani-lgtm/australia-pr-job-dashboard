# 🇦🇺 Australia PR Job Dashboard

A Streamlit dashboard for tracking Australian job opportunities relevant to skilled-migration Permanent Residency, with CV matching, application tracking, and AI-assisted cover letter generation.

## Features

| Feature | Description |
|---|---|
| **Job Database** | 30+ pre-loaded Australian jobs across 9 categories |
| **Live Scraper Stubs** | Extensible scrapers for APS Jobs, Seek, Indeed, university portals |
| **CV Matching Engine** | TF-IDF + keyword scoring to rank every job against your CV |
| **Skills Gap Analysis** | Per-job breakdown of matched/missing skills with tailoring tips |
| **Application Tracker** | Kanban-style pipeline: Bookmarked → Applied → Interview → Offer |
| **Cover Letter Generator** | Category-specific templates merged with your profile |
| **CV Tailoring Tool** | Phrase-by-phrase suggestions to beat ATS and impress hiring managers |

## Job Categories

- Health Economist
- Research Fellow
- Lecturer / Tutor
- Policy Analyst
- Evaluation Specialist
- Data Analyst
- Business Intelligence Analyst
- Economist

## Job Sources

- APS Jobs (Australian Public Service)
- University Portals (ANU, Monash, UQ, UNSW, USyd, UMelb…)
- CSIRO
- Seek & Indeed
- Consulting Firms (Deloitte, KPMG, PwC, EY)
- Government Departments (Treasury, RBA, ACCC, NDIA, DFAT…)

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/australia-pr-job-dashboard.git
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

### 4. Run the dashboard

```bash
streamlit run app.py
```

The dashboard will open at **http://localhost:8501** in your browser.

---

## Project Structure

```
australia-pr-job-dashboard/
├── app.py              # Main Streamlit dashboard (6 pages)
├── config.py           # Categories, sources, keywords, APS classifications
├── database.py         # SQLite layer — init, CRUD for all tables
├── jobs.py             # Sample job data + scraper stubs
├── cv_match.py         # TF-IDF matching engine, skills-gap analysis
├── cover_letter.py     # Cover letter templates (9 categories)
├── requirements.txt    # Python dependencies
├── .gitignore
└── README.md
```

## Database Tables

| Table | Contents |
|---|---|
| `jobs` | Job listings with category, salary, description, URL |
| `applications` | Your applications with status and notes |
| `user_profile` | Your CV text, skills, education, visa status |
| `cover_letters` | Saved cover letters with version history |

---

## Usage Guide

### Setting Up Your Profile
1. Go to **⚙️ Settings**
2. Enter your name, email, phone, LinkedIn URL
3. Select your visa status and target roles
4. Paste your full CV text
5. Save — your CV is now used for all job matching

### Browsing Jobs
1. Go to **🔍 Browse Jobs**
2. Filter by category, source, state, keyword, or salary
3. Each job card shows a **match score** if your CV is saved
4. Click **Details & Actions** to see the full description, requirements, and skills gap
5. Bookmark or mark as applied directly from the card

### Tracking Applications
1. Go to **📋 Applications**
2. Update status, add notes, set follow-up dates
3. Delete stale applications

### Matching Your CV
1. Go to **🎯 CV Matching**
2. Paste or confirm your CV text
3. Click **Score All Jobs** to rank every job
4. Select a job for a detailed skills-gap report and tailoring suggestions

### Generating Cover Letters
1. Go to **✍️ Cover Letters**
2. Select a job from the dropdown
3. Optionally enter the hiring manager's name and personalisation notes
4. Click **Generate Cover Letter**
5. Edit the result in the text area, then save or download

---

## Extending the Scrapers

Scraper stubs are in `jobs.py`. To add live data:

- **APS Jobs**: Use the [APS Jobs Search API](https://www.apsjobs.gov.au) or Playwright-based scraping with a registered session.
- **Seek**: Enrol in the [Seek Talent Search API partner program](https://developer.seek.com).
- **Indeed**: Use the [Indeed Publisher API](https://ads.indeed.com/jobroll/xmlfeed).
- **Universities**: Most Australian universities use PageUp; adapt `fetch_university_jobs()` per portal.

---

## PR / Visa Context

The dashboard is designed around the **Australian Skilled Migration** pathway:
- Jobs tagged `is_pr_relevant = 1` align with ANZSCO skilled occupations
- Target roles map to the **Skilled Occupations List (SOL)** and **MLTSSL**
- Prioritises **ongoing** (permanent) APS and university positions that support points-test claims for age, English, education, and employment

---

## Requirements

- Python 3.11+
- See `requirements.txt` for package versions

No API keys or external services are required to run the dashboard with sample data.

---

## Contributing

Pull requests welcome. Please open an issue first for significant changes.

## License

MIT
