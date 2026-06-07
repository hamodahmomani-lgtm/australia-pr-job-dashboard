"""Central configuration — loads .env, exposes typed constants."""

import os
from pathlib import Path

# ── Load .env if present (never fails if file is missing) ────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=False)
except ImportError:
    pass  # python-dotenv optional; raw env vars still work

# ── Secrets / runtime config ──────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str   = os.getenv("TELEGRAM_CHAT_ID", "")
DB_PATH: str            = os.getenv("DB_PATH", "dashboard.db")
SCRAPE_HOUR: int        = int(os.getenv("SCRAPE_HOUR", "8"))
SCRAPE_MINUTE: int      = int(os.getenv("SCRAPE_MINUTE", "0"))
REQUEST_DELAY: float    = float(os.getenv("REQUEST_DELAY", "2"))
REQUEST_TIMEOUT: int    = int(os.getenv("REQUEST_TIMEOUT", "15"))
MAX_SCRAPER_THREADS: int = int(os.getenv("MAX_SCRAPER_THREADS", "4"))

# ── Domain constants ──────────────────────────────────────────────────────────

JOB_CATEGORIES = [
    "Health Economist",
    "Research Fellow",
    "Lecturer",
    "Tutor",
    "Policy Analyst",
    "Senior Policy Officer",
    "Health Policy Officer",
    "Program Evaluation Officer",
    "Evaluation Specialist",
    "Government Research Officer",
    "Data Analyst",
    "Business Intelligence Analyst",
    "Economist",
]

JOB_SOURCES = [
    "APS Jobs",
    "University Portal",
    "CSIRO",
    "Seek",
    "Consulting Firms",
    "Government Departments",
    "NSW Government",
    "Victoria Government",
    "Queensland Government",
    "SA Government",
    "WA Government",
    "ACT Government",
    "Tasmania Government",
    "NT Government",
]

# Maps Australian state abbreviation → source label used by state gov scrapers
STATE_GOV_SOURCES: dict[str, str] = {
    "NSW": "NSW Government",
    "VIC": "Victoria Government",
    "QLD": "Queensland Government",
    "SA":  "SA Government",
    "WA":  "WA Government",
    "ACT": "ACT Government",
    "TAS": "Tasmania Government",
    "NT":  "NT Government",
}

EMPLOYMENT_TYPES = [
    "Ongoing Full-time",
    "Ongoing Part-time",
    "Non-ongoing",
    "Contract",
    "Casual",
    "Fixed Term",
]

APPLICATION_STATUSES = [
    "Bookmarked",
    "Applied",
    "Phone Screen",
    "Interview",
    "Assessment",
    "Offer",
    "Rejected",
    "Withdrawn",
]

APS_CLASSIFICATIONS = {
    "APS 3-4":    (65_000, 80_000),
    "APS 5-6":    (80_000, 100_000),
    "EL1":        (110_000, 130_000),
    "EL2":        (135_000, 165_000),
    "SES Band 1": (200_000, 270_000),
}

STATES = ["ACT", "NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "Remote"]

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    # ── Keywords are calibrated to Mohammad Almomani's PhD health-economics profile ──
    "Health Economist": [
        # Standard HE job-market terms
        "health economics", "cost-effectiveness", "HTA", "PBAC", "pharmacoeconomics",
        "burden of disease", "QALY", "budget impact", "health technology assessment",
        "economic evaluation", "CEA", "CBA", "Medicare", "healthcare costs",
        "cost utility", "cost benefit", "health policy", "health expenditure",
        "PBS", "TGA", "AIHW", "health system",
        # Mohammad's specific competencies
        "SHARE", "HILDA", "ALSWH", "aged care", "ageing", "healthy ageing",
        "IADL", "functional health", "retirement", "wellbeing", "older adults",
        "longitudinal survey", "panel data", "econometric", "population health",
        "preventive health", "aged-care need", "functional decline",
        "instrumental variables", "fixed effects", "health governance",
        "locus of control", "wellbeing economics",
    ],
    "Research Fellow": [
        # Standard RF terms
        "research fellow", "postdoctoral", "post-doc", "academic research",
        "grant", "publication", "peer-reviewed", "research project", "ARC", "NHMRC",
        "systematic review", "meta-analysis", "RCT", "quantitative research",
        "qualitative research", "mixed methods", "cohort study",
        # Mohammad's specific competencies
        "SHARE data", "HILDA survey", "ALSWH", "longitudinal", "panel data",
        "applied econometrics", "ageing research", "GLO", "Journal of Economic Studies",
        "difference-in-differences", "instrumental variables", "regression discontinuity",
        "event study", "causal inference", "health economics research",
        "economic studies", "labour economics", "population ageing",
    ],
    "Lecturer": [
        # Standard lecturer terms
        "lecturer", "teaching", "curriculum", "undergraduate", "postgraduate",
        "unit coordinator", "higher education", "university", "academic",
        "student learning", "assessment design", "tutorial", "unit convener",
        "course design", "pedagogy", "blended learning",
        # Mohammad's specific competencies
        "economics lecturer", "Python teaching", "coding for business",
        "data visualisation teaching", "applied analytics", "casual academic",
        "sessional academic", "tutorial facilitation", "assessment marking",
        "economics unit", "econometrics teaching", "business program",
        "mathematical economics", "macroeconomics", "microeconomics",
        "Flinders University", "Adelaide University",
    ],
    "Tutor": [
        "tutor", "tutorial", "casual academic", "demonstrator",
        "student support", "marking", "lecturing", "sessional",
        "economics tutor", "Python tutor", "data analysis tutor",
        "applied economics", "statistical analysis tutor",
    ],
    "Policy Analyst": [
        # Standard policy terms
        "policy", "policy analysis", "policy development", "stakeholder",
        "government", "regulation", "legislation", "brief", "cabinet",
        "consultation", "reform", "APS", "public sector", "ministerial",
        "evidence based", "regulatory impact", "cost benefit analysis",
        # Mohammad's specific competencies
        "health policy", "aged care policy", "AIHW", "Department of Health",
        "economic evidence", "retirement policy", "population ageing",
        "evidence synthesis", "policy brief", "EL1", "EL2", "APS level",
        "social policy", "disability policy", "preventive health policy",
        "causal analysis", "impact assessment",
        # Government sector terms
        "policy officer", "policy advice", "policy framework", "policy review",
        "strategic policy", "whole-of-government", "cross-agency",
        "regulatory framework", "governance", "program policy",
        "state government", "public policy", "government department",
    ],
    "Senior Policy Officer": [
        # Core senior policy role terms
        "senior policy", "senior policy officer", "principal policy", "policy lead",
        "policy development", "policy advice", "policy framework", "policy review",
        "strategic policy", "ministerial advice", "cabinet submission",
        "whole-of-government", "cross-agency", "stakeholder engagement",
        "consultation", "regulation", "legislation", "APS EL1", "APS EL2",
        "EL1", "EL2", "senior officer", "lead analyst",
        # Government context
        "public sector", "government department", "state government",
        "federal government", "policy reform", "regulatory reform",
        "evidence-based policy", "policy implementation",
        # Mohammad's competencies
        "health policy", "aged care policy", "social policy", "economic policy",
        "AIHW", "Department of Health", "Treasury", "evidence synthesis",
        "impact assessment", "policy brief", "program evaluation",
        "causal analysis", "population ageing", "preventive health policy",
    ],
    "Health Policy Officer": [
        # Core health policy terms
        "health policy", "health policy officer", "healthcare policy",
        "public health policy", "health system", "health regulation",
        "health program", "health strategy", "health reform",
        "health financing", "health expenditure", "health governance",
        "primary care policy", "hospital policy", "mental health policy",
        "aged care policy", "preventive health", "health promotion",
        # Australian health sector
        "AIHW", "Department of Health", "Medicare", "PBS", "TGA", "NDIS",
        "aged care", "disability policy", "health equity",
        "Australian health system", "health workforce", "health data",
        "NHMRC", "health technology assessment", "HTA", "PBAC",
        # Mohammad's competencies
        "health economics", "cost-effectiveness", "QALY",
        "economic evaluation", "health expenditure analysis",
        "population health", "HILDA", "ALSWH", "SHARE",
        "panel data", "longitudinal", "functional health", "ageing",
        "health outcomes", "health services research",
        # Policy skills
        "policy analysis", "evidence synthesis", "policy brief",
        "stakeholder", "ministerial advice", "government",
    ],
    "Program Evaluation Officer": [
        # Core program evaluation terms
        "program evaluation", "evaluation officer", "monitoring and evaluation",
        "M&E", "evaluation framework", "evaluation methodology",
        "evaluation plan", "evaluation design", "evaluation report",
        "impact assessment", "program outcomes", "program performance",
        "program monitoring", "logic model", "theory of change",
        "formative evaluation", "summative evaluation", "process evaluation",
        "outcome evaluation", "performance measurement", "KPI",
        # Econometric evaluation methods
        "economic evaluation", "quasi-experimental", "natural experiment",
        "counterfactual", "causal inference", "randomised evaluation",
        "difference-in-differences", "DiD", "regression discontinuity", "RDD",
        "instrumental variables", "propensity score", "matching methods",
        "fixed effects", "event study", "interrupted time series",
        # Data and reporting
        "data collection", "survey design", "mixed methods",
        "qualitative research", "quantitative analysis", "statistical analysis",
        "reporting", "dashboard", "stakeholder reporting",
        # Government context
        "government program", "public program", "policy evaluation",
        "APS", "state government", "community program",
        # Mohammad's competencies
        "HILDA", "SHARE", "ALSWH", "Stata", "Python", "R",
        "health program", "aged care program", "social program",
    ],
    "Evaluation Specialist": [
        # Standard evaluation terms
        "evaluation", "program evaluation", "monitoring", "outcomes",
        "logic model", "theory of change", "evaluation framework",
        "formative", "summative", "mixed methods", "KPI",
        "performance measurement", "impact evaluation", "process evaluation",
        # Mohammad's specific econometric evaluation competencies
        "economic evaluation", "instrumental variables", "regression discontinuity",
        "difference-in-differences", "event study", "fixed effects",
        "causal inference", "counterfactual", "RDD", "DiD",
        "HILDA", "SHARE", "longitudinal evaluation", "quasi-experimental",
        "natural experiment", "discrete choice experiment", "cost-quality assessment",
        # Expanded evaluation context
        "evaluation specialist", "evaluation consultant", "evaluation manager",
        "evaluation lead", "health evaluation", "social evaluation",
        "program assessment", "policy assessment", "impact measurement",
    ],
    "Government Research Officer": [
        "research officer", "senior research officer", "policy officer",
        "research analyst", "APS", "EL1", "EL2", "APS 5", "APS 6",
        "government research", "government analyst",
        "AIHW", "Department of Health", "Department of Social Services",
        "Department of Employment", "Treasury", "Productivity Commission",
        "Office of National Statistics", "research analysis",
        "evidence synthesis", "literature review", "data analysis",
        "population health", "aged care", "disability", "health equity",
        "economic research", "social research", "labour market research",
        "policy evidence", "research translation", "health data",
    ],
    "Data Analyst": [
        # Standard DA terms
        "data analysis", "SQL", "Python", "R", "Power BI", "Tableau",
        "data visualisation", "analytics", "statistics", "reporting",
        "dashboard", "ETL", "data modelling", "data cleaning",
        "pandas", "numpy", "machine learning", "statistical modelling",
        # Mohammad's specific competencies
        "Stata", "econometrics", "survey data", "HILDA", "SHARE", "ALSWH",
        "panel data analysis", "fixed effects regression", "longitudinal data",
        "administrative data", "population data", "Excel advanced",
        "energy market analysis", "market data", "quantitative analysis",
    ],
    "Business Intelligence Analyst": [
        # Standard BI terms
        "business intelligence", "BI", "Power BI", "Tableau", "Looker",
        "data warehouse", "ETL", "SQL", "reporting", "dashboard",
        "SSRS", "data modelling", "KPI", "DAX", "data lake",
        "Azure Synapse", "Redshift", "BigQuery", "Snowflake",
        # Mohammad's applicable skills
        "Power BI", "SQL", "Python", "data visualisation", "analytics reporting",
        "energy market analytics", "market analysis", "performance dashboard",
        "executive reporting", "business analytics",
    ],
    "Economist": [
        # Standard economist terms
        "economist", "economic analysis", "econometrics", "modelling",
        "macroeconomics", "microeconomics", "labour market", "forecasting",
        "statistical analysis", "Treasury", "RBA", "ACCC",
        "cost benefit", "economic modelling", "Stata",
        "productivity", "welfare analysis",
        # Mohammad's specific competencies
        "applied econometrics", "instrumental variables", "IV estimation",
        "regression discontinuity", "RDD", "difference-in-differences", "DiD",
        "fixed effects", "panel data", "HILDA", "SHARE",
        "labour economics", "health economics", "population economics",
        "ageing economics", "wellbeing economics", "applied microeconomics",
        "causal inference", "natural experiment", "quasi-experimental design",
    ],
}

# Search terms calibrated to Mohammad Almomani's target roles and research profile
SCRAPE_SEARCH_TERMS = [
    # Health economics & research
    "health economist",
    "research fellow health economics",
    "research fellow economics",
    "ageing research fellow",
    "health economics consultant",
    "applied economist",
    # Policy roles
    "policy analyst health",
    "senior policy officer",
    "policy officer health",
    "health policy officer",
    "policy analyst government",
    "senior policy analyst",
    # Evaluation roles
    "evaluation specialist",
    "program evaluation officer",
    "evaluation officer",
    "monitoring and evaluation",
    # Research officer roles
    "research officer",
    "senior research officer",
    "research analyst government",
    "research officer aged care",
    # Data & economics roles
    "economist government",
    "data analyst government",
    "business intelligence analyst",
    "econometrics analyst",
    # Academic roles
    "lecturer economics",
    "casual academic economics",
]

# ── Default user profile — Mohammad Almomani ──────────────────────────────────
DEFAULT_PROFILE = {
    "name":              "Mohammad Almomani",
    "email":             "Mohammad.almomani@adelaide.edu.au",
    "phone":             "+61452608631",
    "linkedin":          "linkedin.com/in/mohammadalmomani",
    "visa_status":       "Skilled Independent (189)",
    "location":          "Adelaide, South Australia",
    "qualification":     "PhD Economics, Flinders University (2025)",
    "specialisation":    "Health Economics & Applied Econometrics",
    "years_experience":  7,
    "institutions":      "Flinders University / Adelaide University",
    "research_focus": (
        "Health economics, ageing, functional health, retirement policy, "
        "and wellbeing using SHARE, HILDA, and ALSWH panel datasets. "
        "Causal inference: IV, RDD, DiD, event-study designs."
    ),
    "publications":      10,
    "data_skills":       "Stata, Python, R, Power BI, SQL, Microsoft Excel",
    "econometric_methods": (
        "Fixed Effects & IV, Dynamic DiD, Event Study, Fuzzy RDD, "
        "Economic Evaluation, Discrete Choice Experiments"
    ),
    "aps_classification": "APS 5–6 / EL1",
    "teaching": (
        "Casual Academic at Adelaide University and Flinders University; "
        "delivered Python, econometrics, economics, and data visualisation units"
    ),
    "affiliations": "Affiliate Researcher, Global Labor Organization (GLO)",
}
