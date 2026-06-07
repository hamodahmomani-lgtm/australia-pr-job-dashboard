"""
Job layer — sample data (seed) + wrappers that call real scrapers.

The SAMPLE_JOBS list uses FIXED dates (not _today()) so the UNIQUE
constraint (title, organization, url) works correctly on re-seed.
"""

from datetime import date

# ── Fixed-date helper ─────────────────────────────────────────────────────────
# We anchor to the date the project was created so sample jobs look recent
# but never shift, preventing duplicate inserts on every re-seed.

_SEED_DATE = "2026-06-05"   # project creation date — do not change


def _close(days: int) -> str:
    from datetime import datetime, timedelta
    base = datetime.strptime(_SEED_DATE, "%Y-%m-%d")
    return (base + timedelta(days=days)).strftime("%Y-%m-%d")


# ── Sample jobs (seeded once) ─────────────────────────────────────────────────

SAMPLE_JOBS = [
    # Health Economist
    {
        "title": "Health Economist",
        "organization": "Australian Institute of Health and Welfare (AIHW)",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Health Economist", "source": "APS Jobs",
        "salary_min": 95_000, "salary_max": 110_000,
        "description": (
            "We are seeking a Health Economist to join our Health Expenditure and "
            "Financing team. You will conduct cost-effectiveness analyses, prepare "
            "health expenditure reports, and support HTA submissions to the PBAC. "
            "The role involves applying economic modelling to inform health policy "
            "decisions and publishing findings in peer-reviewed outlets."
        ),
        "requirements": (
            "• Masters or PhD in Health Economics, Economics, or related field\n"
            "• Experience with cost-effectiveness / cost-utility analysis (CEA, CUA)\n"
            "• Proficiency in R, Stata, or Python for economic modelling\n"
            "• Strong written communication and policy-brief writing skills\n"
            "• Experience with PBAC or TGA processes desirable\n"
            "• Australian citizen or PR holder"
        ),
        "url": "https://www.apsjobs.gov.au/s/job-details?jobId=aihw-health-econ-2026",
        "posted_date": _SEED_DATE, "closing_date": _close(21),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Senior Health Economist",
        "organization": "Deloitte Access Economics",
        "location": "Sydney, NSW", "state": "NSW",
        "category": "Health Economist", "source": "Consulting Firms",
        "salary_min": 115_000, "salary_max": 140_000,
        "description": (
            "Deloitte Access Economics is looking for a Senior Health Economist to "
            "lead economic evaluations for pharmaceutical, medical device, and "
            "government health clients. Responsibilities include conducting BIA, CEA, "
            "and CBA, managing client relationships, and mentoring junior economists."
        ),
        "requirements": (
            "• PhD or Masters in Health Economics\n"
            "• 4+ years experience in economic evaluation and PBAC submissions\n"
            "• Strong Excel modelling and R/Python skills\n"
            "• Excellent stakeholder management skills"
        ),
        "url": "https://apply.deloitte.com/careers/SearchJobs?Keywords=health+economist&Country=AU",
        "posted_date": _SEED_DATE, "closing_date": _close(28),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Health Economics Analyst",
        "organization": "KPMG Australia",
        "location": "Melbourne, VIC", "state": "VIC",
        "category": "Health Economist", "source": "Consulting Firms",
        "salary_min": 90_000, "salary_max": 115_000,
        "description": (
            "Join KPMG Health's economics team to support economic analyses for "
            "hospital networks, health insurers, and Commonwealth health programs. "
            "You will design evaluation frameworks, analyse health data (APDC, MBS/PBS), "
            "and present findings to senior government stakeholders."
        ),
        "requirements": (
            "• Degree in Health Economics, Economics, or Public Health\n"
            "• Proficiency in Stata, R, or SAS\n"
            "• Knowledge of Australian health system and Medicare"
        ),
        "url": "https://home.kpmg/au/en/home/careers/find-a-job.html",
        "posted_date": _SEED_DATE, "closing_date": _close(18),
        "employment_type": "Ongoing Full-time",
    },
    # Research Fellow
    {
        "title": "Research Fellow – Health Policy",
        "organization": "Australian National University (ANU)",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Research Fellow", "source": "University Portal",
        "salary_min": 100_000, "salary_max": 118_000,
        "description": (
            "The ANU College of Health and Medicine invites applications for a "
            "Research Fellow conducting independent research in health systems and "
            "health policy. The successful candidate will lead grant applications, "
            "publish high-impact research, and contribute to postgraduate supervision."
        ),
        "requirements": (
            "• PhD in Public Health, Health Economics, or Health Policy\n"
            "• Strong publication record (Q1/Q2 journals)\n"
            "• Track record with NHMRC or ARC competitive grants\n"
            "• Quantitative and/or qualitative research skills"
        ),
        "url": "https://jobs.anu.edu.au/cw/en/listing/",
        "posted_date": _SEED_DATE, "closing_date": _close(25),
        "employment_type": "Fixed Term",
    },
    {
        "title": "Postdoctoral Research Fellow – Economic Policy",
        "organization": "Melbourne Institute of Applied Economic and Social Research",
        "location": "Melbourne, VIC", "state": "VIC",
        "category": "Research Fellow", "source": "University Portal",
        "salary_min": 97_000, "salary_max": 115_000,
        "description": (
            "The Melbourne Institute seeks a Postdoctoral Research Fellow to work "
            "on ARC-funded projects on labour market economics and social policy "
            "evaluation. Conduct empirical research, publish results, and assist "
            "with grant applications."
        ),
        "requirements": (
            "• Recently conferred PhD in Economics or Public Policy\n"
            "• Strong applied econometrics (Stata, R, or Python)\n"
            "• Experience with administrative data or large survey datasets\n"
            "• At least one peer-reviewed publication"
        ),
        "url": "https://jobs.unimelb.edu.au/cw/en/listing/",
        "posted_date": _SEED_DATE, "closing_date": _close(22),
        "employment_type": "Fixed Term",
    },
    {
        "title": "Research Fellow – Data Science & Health",
        "organization": "CSIRO Health & Biosecurity",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Research Fellow", "source": "CSIRO",
        "salary_min": 103_000, "salary_max": 125_000,
        "description": (
            "CSIRO is looking for a Research Fellow to develop AI-driven analytics "
            "tools for population health surveillance."
        ),
        "requirements": (
            "• PhD in Data Science, Biostatistics, or Computational Epidemiology\n"
            "• Strong Python/R for data analysis and machine learning\n"
            "• Experience with health administrative data\n"
            "• Peer-reviewed publication record"
        ),
        "url": "https://jobs.csiro.au/cw/en/listing/",
        "posted_date": _SEED_DATE, "closing_date": _close(20),
        "employment_type": "Fixed Term",
    },
    # Lecturer
    {
        "title": "Lecturer in Health Economics",
        "organization": "University of Queensland",
        "location": "Brisbane, QLD", "state": "QLD",
        "category": "Lecturer", "source": "University Portal",
        "salary_min": 107_000, "salary_max": 127_000,
        "description": (
            "UQ's School of Public Health invites applications for a Lecturer (Level B) "
            "in Health Economics. Deliver undergraduate and postgraduate units, supervise "
            "higher-degree research students, and contribute to research and consultancy."
        ),
        "requirements": (
            "• PhD in Health Economics, Economics, or related discipline\n"
            "• Evidence of quality teaching at tertiary level\n"
            "• Research track record in health economics\n"
            "• Capacity to attract competitive research funding"
        ),
        "url": "https://careers.uq.edu.au/cw/en/listing/",
        "posted_date": _SEED_DATE, "closing_date": _close(30),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Lecturer – Public Policy",
        "organization": "Australian National University (ANU)",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Lecturer", "source": "University Portal",
        "salary_min": 105_000, "salary_max": 125_000,
        "description": (
            "Crawford School of Public Policy at ANU invites applications for a "
            "Lecturer in Public Policy covering policy analysis, program evaluation, "
            "and evidence-based policy-making at the graduate level."
        ),
        "requirements": (
            "• PhD in Public Policy, Economics, or Political Science\n"
            "• Excellence in teaching and research\n"
            "• Government engagement experience\n"
            "• Strong publication profile"
        ),
        "url": "https://jobs.anu.edu.au/cw/en/listing/",
        "posted_date": _SEED_DATE, "closing_date": _close(28),
        "employment_type": "Ongoing Full-time",
    },
    # Tutor
    {
        "title": "Casual Academic – Economics Tutor",
        "organization": "University of New South Wales (UNSW)",
        "location": "Sydney, NSW", "state": "NSW",
        "category": "Tutor", "source": "University Portal",
        "salary_min": 45_000, "salary_max": 60_000,
        "description": (
            "UNSW Business School seeks casual academics to tutor undergraduate "
            "Economics units: Microeconomics, Macroeconomics, Health Economics. "
            "Duties: running tutorials, marking assignments, student support."
        ),
        "requirements": (
            "• Masters or PhD in Economics preferred\n"
            "• Strong communication skills\n"
            "• Availability for scheduled tutorials"
        ),
        "url": "https://www.jobs.unsw.edu.au/cw/en/listing/",
        "posted_date": _SEED_DATE, "closing_date": _close(12),
        "employment_type": "Casual",
    },
    # Policy Analyst
    {
        "title": "Policy Analyst – Health Financing",
        "organization": "Department of Health and Aged Care",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Policy Analyst", "source": "APS Jobs",
        "salary_min": 85_000, "salary_max": 100_000,
        "description": (
            "APS 6 Policy Analyst. Support health financing policy development, "
            "analyse health expenditure data, draft ministerial correspondence, "
            "engage with stakeholders across the health sector."
        ),
        "requirements": (
            "• Degree in Economics, Public Policy, or related field\n"
            "• Policy analysis and writing skills\n"
            "• Understanding of Medicare and Australian health system\n"
            "• Australian citizen"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(17),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Senior Policy Analyst – Economic Reform",
        "organization": "Department of the Prime Minister and Cabinet",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Policy Analyst", "source": "APS Jobs",
        "salary_min": 110_000, "salary_max": 130_000,
        "description": (
            "EL1 Senior Policy Analyst supporting whole-of-government economic "
            "reform. Develop Cabinet submissions, coordinate across agencies, "
            "provide strategic economic policy advice to senior ministers."
        ),
        "requirements": (
            "• Degree in Economics, Law, or Public Policy\n"
            "• 5+ years APS or equivalent policy experience\n"
            "• Demonstrated ability to draft Cabinet documents\n"
            "• Baseline or higher security clearance"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(19),
        "employment_type": "Ongoing Full-time",
    },
    # Evaluation Specialist
    {
        "title": "Program Evaluation Specialist",
        "organization": "Australian National Audit Office (ANAO)",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Evaluation Specialist", "source": "APS Jobs",
        "salary_min": 98_000, "salary_max": 118_000,
        "description": (
            "Design and conduct performance audits of Commonwealth programs. "
            "Develop evaluation methodologies, analyse program data, prepare "
            "audit reports for the Australian Parliament."
        ),
        "requirements": (
            "• Degree in Public Administration, Economics, or related field\n"
            "• Program/policy evaluation methods including logic models\n"
            "• Report writing at executive level\n"
            "• Negative Vetting 1 clearance eligibility"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(20),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Evaluation Consultant – Social Policy",
        "organization": "PwC Australia",
        "location": "Sydney, NSW", "state": "NSW",
        "category": "Evaluation Specialist", "source": "Consulting Firms",
        "salary_min": 105_000, "salary_max": 135_000,
        "description": (
            "Lead program evaluations for Federal and State government clients. "
            "Design evaluation frameworks, conduct mixed-methods data analysis, "
            "write reports, and present findings to executive stakeholders."
        ),
        "requirements": (
            "• Degree in Economics, Social Policy, or Public Policy\n"
            "• 3–5 years evaluation experience\n"
            "• Mixed methods research skills"
        ),
        "url": "https://www.pwc.com.au/careers/search-jobs.html",
        "posted_date": _SEED_DATE, "closing_date": _close(24),
        "employment_type": "Ongoing Full-time",
    },
    # Government Research Officer
    {
        "title": "Research Officer – Ageing and Aged Care",
        "organization": "Australian Institute of Health and Welfare (AIHW)",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Government Research Officer", "source": "APS Jobs",
        "salary_min": 88_000, "salary_max": 105_000,
        "description": (
            "APS 6 Research Officer to contribute to AIHW's aged care monitoring "
            "and reporting work. Analyse HILDA, My Aged Care, and administrative "
            "datasets; prepare statistical reports and research briefs; "
            "collaborate with policy teams across the Department of Health."
        ),
        "requirements": (
            "• Degree in Economics, Public Health, Social Science, or Statistics\n"
            "• Experience with HILDA, ALSWH, or similar longitudinal surveys\n"
            "• Stata, R, or Python for quantitative analysis\n"
            "• Strong research writing and plain-language communication\n"
            "• Australian citizen"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(23),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Senior Research Officer – Economic Evidence",
        "organization": "Productivity Commission",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Government Research Officer", "source": "APS Jobs",
        "salary_min": 100_000, "salary_max": 120_000,
        "description": (
            "EL1 Senior Research Officer to support Productivity Commission inquiries "
            "into social services, aged care, disability, and health sectors. "
            "Analyse economic evidence, conduct literature reviews, model policy "
            "impacts using causal econometric methods."
        ),
        "requirements": (
            "• PhD or Honours in Economics or related discipline\n"
            "• Applied econometrics — panel data, IV, quasi-experimental design\n"
            "• Stata, R, or Python for quantitative modelling\n"
            "• Excellent analytical writing for public audience"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(26),
        "employment_type": "Ongoing Full-time",
    },
    # Data Analyst
    {
        "title": "Data Analyst – Health Statistics",
        "organization": "Australian Bureau of Statistics (ABS)",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Data Analyst", "source": "APS Jobs",
        "salary_min": 80_000, "salary_max": 96_000,
        "description": (
            "Manage and analyse large administrative health datasets. "
            "Data linkage, quality assurance, statistical analysis, and "
            "production of statistical publications."
        ),
        "requirements": (
            "• Degree in Statistics, Epidemiology, Data Science, or related field\n"
            "• Proficiency in R, Python, or SAS\n"
            "• Experience with large-scale administrative data\n"
            "• Australian citizen"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(16),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Senior Data Analyst",
        "organization": "National Disability Insurance Agency (NDIA)",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Data Analyst", "source": "APS Jobs",
        "salary_min": 95_000, "salary_max": 112_000,
        "description": (
            "Support actuarial and economic analysis of the NDIS scheme. "
            "Build analytical models, produce Power BI dashboards, "
            "and advise on data-driven insights to improve scheme sustainability."
        ),
        "requirements": (
            "• Degree in Statistics, Actuarial Studies, Data Science, or Economics\n"
            "• Advanced SQL and Python\n"
            "• Experience with Power BI or Tableau"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(18),
        "employment_type": "Ongoing Full-time",
    },
    # Business Intelligence Analyst
    {
        "title": "Business Intelligence Analyst",
        "organization": "Services Australia",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Business Intelligence Analyst", "source": "APS Jobs",
        "salary_min": 85_000, "salary_max": 100_000,
        "description": (
            "Develop Power BI dashboards for executive decision-making. "
            "ETL pipeline development, data warehouse management, "
            "stakeholder consultation to define BI requirements."
        ),
        "requirements": (
            "• Degree in IT, Information Systems, or related field\n"
            "• Power BI proficiency (DAX, M Query)\n"
            "• Strong SQL and ETL skills\n"
            "• Australian citizen or PR holder"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(15),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Senior BI Developer",
        "organization": "EY Australia",
        "location": "Sydney, NSW", "state": "NSW",
        "category": "Business Intelligence Analyst", "source": "Consulting Firms",
        "salary_min": 110_000, "salary_max": 140_000,
        "description": (
            "Deliver analytics solutions for financial services and government clients. "
            "Architect data models, develop Tableau/Power BI dashboards, "
            "lead client workshops."
        ),
        "requirements": (
            "• 5+ years BI development experience\n"
            "• Expert Power BI or Tableau\n"
            "• Strong SQL and database design\n"
            "• Cloud data platforms (Azure Synapse, Redshift, BigQuery)"
        ),
        "url": "https://careers.ey.com/ey/search/?q=BI+developer&country=Australia",
        "posted_date": _SEED_DATE, "closing_date": _close(21),
        "employment_type": "Ongoing Full-time",
    },
    # Economist
    {
        "title": "Economist – Macroeconomic Analysis",
        "organization": "Reserve Bank of Australia (RBA)",
        "location": "Sydney, NSW", "state": "NSW",
        "category": "Economist", "source": "Government Departments",
        "salary_min": 102_000, "salary_max": 125_000,
        "description": (
            "Conduct research on Australian macroeconomic conditions, write "
            "Bulletin articles, contribute to the Statement on Monetary Policy. "
            "Econometric modelling, literature reviews, presenting to senior management."
        ),
        "requirements": (
            "• PhD or Masters in Economics with strong econometrics background\n"
            "• Research experience in macroeconomics or monetary policy\n"
            "• Proficiency in Matlab, R, or Python\n"
            "• High-quality research publications desirable"
        ),
        "url": "https://www.rba.gov.au/careers/",
        "posted_date": _SEED_DATE, "closing_date": _close(22),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Senior Economist",
        "organization": "Australian Treasury",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Economist", "source": "APS Jobs",
        "salary_min": 113_000, "salary_max": 135_000,
        "description": (
            "EL1 Senior Economist. Lead analysis of the Australian economy, "
            "contribute to MYEFO and Budget forecasts. "
            "Strong modelling capabilities, write briefings for the Treasurer."
        ),
        "requirements": (
            "• PhD or Honours in Economics\n"
            "• Economic forecasting and modelling experience\n"
            "• Excellent analytical and writing skills\n"
            "• APS security clearance eligibility"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(20),
        "employment_type": "Ongoing Full-time",
    },
    {
        "title": "Economist – Productivity Commission",
        "organization": "Productivity Commission",
        "location": "Canberra, ACT", "state": "ACT",
        "category": "Economist", "source": "APS Jobs",
        "salary_min": 95_000, "salary_max": 120_000,
        "description": (
            "Contribute to public inquiries and research projects covering "
            "microeconomic and social policy topics. Rigorous research, "
            "prepare inquiry reports, engage with public submissions."
        ),
        "requirements": (
            "• PhD or Honours in Economics\n"
            "• Strong quantitative research and writing skills\n"
            "• Ability to engage constructively with diverse stakeholders"
        ),
        "url": "https://www.apsjobs.gov.au/s/search",
        "posted_date": _SEED_DATE, "closing_date": _close(25),
        "employment_type": "Ongoing Full-time",
    },
]


# ── Public scraping wrappers ──────────────────────────────────────────────────

def refresh_jobs(scraper_name: str | None = None, keywords: list[str] | None = None) -> dict:
    """
    Run one or all scrapers and save results to the database.
    Returns a summary dict.
    """
    if scraper_name:
        from scrapers.coordinator import run_scraper
        return run_scraper(scraper_name, keywords)
    else:
        from scrapers.coordinator import run_all_scrapers
        return run_all_scrapers(keywords)
