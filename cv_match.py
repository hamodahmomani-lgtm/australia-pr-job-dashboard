"""
CV matching engine — calibrated to Mohammad Almomani's PhD health-economics profile.

Key features:
  - TF-IDF cosine (70%) + domain keyword overlap (30%) composite score
  - PROFILE_CV_TEXT provides a pre-built synthetic CV for matching when
    no uploaded CV is available (i.e. first run / no CV uploaded yet)
  - IDF weights domain-specific terms (Stata, SHARE, IV) more than generic ones
  - PR_OCCUPATION_SCORES maps each category to ANZSCO code + skilled-visa eligibility
  - detect_pr_relevance() returns a plain-English eligibility note for any job
"""

import re
import math
import logging
from collections import Counter
from config import CATEGORY_KEYWORDS, DEFAULT_PROFILE

logger = logging.getLogger(__name__)


# ── Pre-built profile text ────────────────────────────────────────────────────
# Used when no CV file has been uploaded so the matching engine still returns
# sensible scores based on Mohammad's known background.

PROFILE_CV_TEXT = (
    "PhD Economics Flinders University 2025 health economics applied econometrics "
    "ageing wellbeing older adults functional health IADL retirement policy "
    "SHARE HILDA ALSWH longitudinal panel data fixed effects instrumental variables "
    "regression discontinuity difference-in-differences DiD event study RDD causal inference "
    "quasi-experimental natural experiment identification strategy "
    "Stata Python R Power BI SQL Microsoft Excel data visualisation "
    "economic evaluation cost-effectiveness CEA CBA health technology assessment "
    "health governance population health preventive health aged care aged-care need "
    "functional decline locus of control volunteering wellbeing economics "
    "casual academic teaching Python coding for business econometrics "
    "data visualisation economics tutorial assessment marking "
    "Journal of Economic Studies International Journal of Health Governance "
    "Applied Economics Health Education Journal of Adult Protection "
    "Biodemography Social Biology peer-reviewed publications "
    "labour economics population economics health policy social policy "
    "Aboriginal Torres Strait Islander AIHW Department of Health "
    "research fellow research analysis policy analysis data analysis "
    "GLO Global Labor Organization Flinders University Adelaide University "
    "MA Economics Yarmouk University Jordan energy market analyst Mubadra Qatar "
    "teaching assistant mathematical economics macroeconomics microeconomics "
    "NHMRC ARC grant research project publication record "
    "master economics business economics bachelor degree "
    "South Australia Adelaide Australia "
)


# ── PR / skilled-visa occupation map ─────────────────────────────────────────
# MLTSSL = Medium & Long-term Strategic Skills List (eligible for 189/190/491/186)
# Based on ANZSCO 6th edition and DIBP occupation lists (verify current list at
# immi.homeaffairs.gov.au before making any visa decisions).

PR_OCCUPATION_SCORES: dict[str, dict] = {
    "Health Economist": {
        "anzsco": "224111",
        "pr_eligible": True,
        "mltssl": True,
        "priority": 1,
        "notes": "MLTSSL — eligible for 189/190/491/186 visa streams.",
    },
    "Economist": {
        "anzsco": "224411",
        "pr_eligible": True,
        "mltssl": True,
        "priority": 1,
        "notes": "MLTSSL — eligible for 189/190/491/186 visa streams.",
    },
    "Research Fellow": {
        "anzsco": "210299",
        "pr_eligible": True,
        "mltssl": True,
        "priority": 2,
        "notes": "University research role — MLTSSL; strong skills-assessment pathway.",
    },
    "Lecturer": {
        "anzsco": "242111",
        "pr_eligible": True,
        "mltssl": True,
        "priority": 2,
        "notes": "University Lecturer on MLTSSL — strong PR pathway.",
    },
    "Government Research Officer": {
        "anzsco": "224411",
        "pr_eligible": True,
        "mltssl": True,
        "priority": 2,
        "notes": "Maps to Economist (224411) on MLTSSL.",
    },
    "Policy Analyst": {
        "anzsco": "224212",
        "pr_eligible": True,
        "mltssl": False,
        "priority": 3,
        "notes": "Management & Organisation Analyst — check current STSOL/MLTSSL.",
    },
    "Evaluation Specialist": {
        "anzsco": "224212",
        "pr_eligible": True,
        "mltssl": False,
        "priority": 3,
        "notes": "Organisation Analyst family — verify current list.",
    },
    "Data Analyst": {
        "anzsco": "261111",
        "pr_eligible": True,
        "mltssl": False,
        "priority": 3,
        "notes": "ICT Business Analyst — check current STSOL for state sponsorship.",
    },
    "Business Intelligence Analyst": {
        "anzsco": "261111",
        "pr_eligible": True,
        "mltssl": False,
        "priority": 3,
        "notes": "ICT Business Analyst — check current STSOL for state sponsorship.",
    },
    "Tutor": {
        "anzsco": "249299",
        "pr_eligible": False,
        "mltssl": False,
        "priority": 5,
        "notes": "Casual/sessional — usually insufficient for a skilled-visa nomination.",
    },
}


# ── Domain-specific IDF boosts ────────────────────────────────────────────────
# Terms that appear in many generic job ads get low IDF.
# Mohammad's domain terms that discriminate good matches get high IDF.

_HIGH_IDF_TERMS = {
    # Econometric methods
    "stata", "hilda", "share", "alswh", "iadl", "econometrics", "econometric",
    "instrumental variables", "regression discontinuity", "rdd",
    "difference-in-differences", "did", "event study", "fixed effects",
    "causal inference", "quasi-experimental", "panel data",
    # Health economics domain
    "pbac", "qaly", "hta", "pharmacoeconomics", "cost-effectiveness",
    "health technology assessment", "cost utility", "aged care",
    "aihw", "aged-care", "functional health", "wellbeing economics",
    # Research skills
    "nhmrc", "arc", "peer-reviewed", "postdoctoral", "post-doc",
    "glm", "logit", "probit", "tobit",
    # BI / data stack
    "power bi", "dax", "azure synapse", "bigquery", "snowflake", "looker",
    # APS context
    "el1", "el2", "aps 5", "aps 6", "ministerial", "cabinet submission",
}

_LOW_IDF_TERMS = {
    "experience", "skills", "strong", "work", "team", "role", "ability",
    "knowledge", "including", "within", "develop", "manage", "support",
    "degree", "relevant", "demonstrated", "excellent", "communication",
    "stakeholder", "senior", "position", "opportunity", "working",
    "required", "provide", "ensure", "quality", "key", "highly",
}


# ── Text helpers ──────────────────────────────────────────────────────────────

_STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "as","by","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","must",
    "can","need","from","not","this","that","these","those","it","its","we",
    "our","you","your","they","their","all","some","any","each","both","more",
    "also","other","about","into","through","during","including","within",
    "across","such","than","so","up","out","if","who","which","what","when",
    "where","how","very","just","only","even","still","yet","though","although",
}


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens = re.findall(r"[a-z][a-z\-']*[a-z]|[a-z]{3,}", text)
    return [t for t in tokens if t not in _STOPWORDS]


def _ngrams(tokens: list[str], n: int) -> list[str]:
    return [" ".join(tokens[i: i + n]) for i in range(len(tokens) - n + 1)]


def extract_keywords(text: str, top_n: int = 30) -> list[str]:
    if not text:
        return []
    tokens = _tokenize(text)
    uni = Counter(tokens)
    bi  = Counter(_ngrams(tokens, 2))
    combined: dict[str, float] = {k: v * 1.8 for k, v in bi.items()}
    combined.update({k: float(v) for k, v in uni.items() if k not in combined})
    return sorted(combined, key=combined.__getitem__, reverse=True)[:top_n]


# ── TF-IDF ────────────────────────────────────────────────────────────────────

def _tf(tokens: list[str]) -> dict[str, float]:
    count = Counter(tokens)
    total = max(len(tokens), 1)
    return {k: v / total for k, v in count.items()}


def _idf(term: str) -> float:
    """
    Approximate IDF without a corpus.
    Domain-specific terms Mohammad uses get elevated IDF so they
    discriminate good matches from generic ones.
    """
    t = term.lower()
    if t in _LOW_IDF_TERMS:
        return 0.4
    if t in _HIGH_IDF_TERMS:
        return 2.5
    # Bigrams are generally more specific
    if " " in t:
        return 2.0
    if len(t) <= 3:
        return 0.6
    if len(t) >= 8:
        return 1.4
    return 1.0


def _tfidf(text: str) -> dict[str, float]:
    tokens = _tokenize(text) + _ngrams(_tokenize(text), 2)
    tf_vals = _tf(tokens)
    return {t: v * _idf(t) for t, v in tf_vals.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    shared = set(a) & set(b)
    if not shared:
        return 0.0
    dot = sum(a[k] * b[k] for k in shared)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Core scoring ──────────────────────────────────────────────────────────────

def calculate_match_score(
    cv_text: str, job_description: str, job_requirements: str = ""
) -> float:
    """
    Return an honest 0–100 match score.

    Composite:
      70% TF-IDF cosine similarity (CV vs combined job text)
      30% domain keyword overlap (category-specific vocabulary)

    When cv_text is empty, falls back to PROFILE_CV_TEXT so scores are
    meaningful even before the user uploads a CV file.

    Calibration reference (Mohammad's profile):
      ~30   : unrelated job (Nurse, IT project manager)
      ~45–55: some overlap (generic data analyst, junior policy)
      ~60–70: good match (APS economist, policy analyst)
      ~75+  : very strong match (health economist, research fellow)
    """
    effective_cv = cv_text.strip() or PROFILE_CV_TEXT
    if not (job_description or job_requirements):
        return 0.0

    combined_job = f"{job_description} {job_requirements}"
    cv_vec  = _tfidf(effective_cv)
    job_vec = _tfidf(combined_job)

    cosine_score = _cosine(cv_vec, job_vec)

    # Domain keyword component — words in CV AND job description
    all_domain_kws = [kw for kws in CATEGORY_KEYWORDS.values() for kw in kws]
    cv_lower  = effective_cv.lower()
    job_lower = combined_job.lower()
    matched   = sum(1 for kw in all_domain_kws if kw.lower() in cv_lower and kw.lower() in job_lower)
    kw_ratio  = matched / max(len(all_domain_kws) * 0.12, 1)
    kw_score  = min(kw_ratio, 1.0)

    # Scale cosine 0–0.45 → 0–100 (0.45 is a very high cosine for long documents)
    cosine_100 = min(cosine_score / 0.45, 1.0) * 100
    raw = cosine_100 * 0.70 + kw_score * 100 * 0.30

    return round(min(raw, 100.0), 1)


def get_matched_keywords(cv_text: str, job_text: str) -> list[str]:
    effective_cv = cv_text.strip() or PROFILE_CV_TEXT
    cv_lower  = effective_cv.lower()
    job_lower = job_text.lower()
    all_kws   = [kw for kws in CATEGORY_KEYWORDS.values() for kw in kws]
    return sorted({kw for kw in all_kws if kw.lower() in cv_lower and kw.lower() in job_lower})


def get_missing_keywords(cv_text: str, job_text: str, category: str = "") -> list[str]:
    effective_cv = (cv_text.strip() or PROFILE_CV_TEXT).lower()
    job_lower = job_text.lower()
    if category and category in CATEGORY_KEYWORDS:
        kws = CATEGORY_KEYWORDS[category]
    else:
        inferred = detect_category(job_text)
        kws = CATEGORY_KEYWORDS.get(inferred, [])
    return [kw for kw in kws if kw.lower() in job_lower and kw.lower() not in effective_cv]


def get_skills_gap(cv_text: str, job: dict) -> dict:
    job_text = f"{job.get('description','')} {job.get('requirements','')}"
    category = job.get("category") or detect_category(job_text)

    matched = get_matched_keywords(cv_text, job_text)
    missing = get_missing_keywords(cv_text, job_text, category)
    score   = calculate_match_score(cv_text, job.get("description",""), job.get("requirements",""))

    recs = []
    if missing:
        recs.append(f"Align these CV terms to the JD: {', '.join(missing[:5])}")
    if score < 40:
        recs.append("Low match — consider whether this role aligns with your target occupation for PR.")
    elif score < 60:
        recs.append("Moderate match — add missing keywords and quantify your achievements.")
    else:
        recs.append("Strong match — ensure these skills appear prominently in your CV's first page.")

    # Add PR context
    pr_info = PR_OCCUPATION_SCORES.get(category, {})
    if pr_info.get("pr_eligible"):
        recs.append(f"PR-eligible occupation (ANZSCO {pr_info.get('anzsco','')}) — {pr_info.get('notes','')}")
    elif pr_info:
        recs.append(f"Note: {pr_info.get('notes','Check current skilled occupation lists.')}")

    return {
        "score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "coverage_pct": round(
            len(matched) / max(len(matched) + len(missing), 1) * 100, 1
        ),
        "recommendations": recs,
        "pr_info": pr_info,
    }


def detect_pr_relevance(job: dict) -> dict:
    """
    Return PR-eligibility info for a job based on its detected or stored category.
    Returns a dict with keys: category, anzsco, pr_eligible, mltssl, priority, notes.
    """
    cat = job.get("category") or detect_category(
        f"{job.get('title','')} {job.get('description','')} {job.get('requirements','')}"
    )
    pr = PR_OCCUPATION_SCORES.get(cat, {
        "anzsco": "unknown",
        "pr_eligible": None,
        "mltssl": False,
        "priority": 4,
        "notes": "Category not mapped — verify ANZSCO manually.",
    })
    return {"category": cat, **pr}


def score_jobs(cv_text: str, jobs: list[dict]) -> list[dict]:
    scored = []
    for job in jobs:
        s = calculate_match_score(
            cv_text, job.get("description",""), job.get("requirements","")
        )
        # Boost score slightly for MLTSSL-eligible roles (Mohammad's PR priority)
        pr_info = PR_OCCUPATION_SCORES.get(job.get("category",""), {})
        if pr_info.get("mltssl"):
            s = min(s + 5, 100)
        scored.append({**job, "match_score": s})
    return sorted(scored, key=lambda x: x["match_score"], reverse=True)


def detect_category(text: str) -> str:
    """Return the best-matching job category for the given text."""
    text_lower = text.lower()
    best, best_count = "Economist", 0
    for cat, kws in CATEGORY_KEYWORDS.items():
        count = sum(1 for kw in kws if kw.lower() in text_lower)
        if count > best_count:
            best_count = count
            best = cat
    return best


def tailor_cv_suggestions(cv_text: str, job: dict) -> str:
    gap = get_skills_gap(cv_text, job)
    pr  = gap.get("pr_info", {})

    lines = [
        f"=== CV Tailoring: {job['title']} @ {job['organization']} ===",
        f"Match Score    : {gap['score']:.0f} / 100",
        f"Skill Coverage : {gap['coverage_pct']}%",
    ]

    if pr:
        mltssl_tag = "MLTSSL ✔" if pr.get("mltssl") else "STSOL / verify"
        pr_tag = "PR-eligible" if pr.get("pr_eligible") else "Not PR-eligible"
        lines.append(
            f"PR Relevance   : {pr_tag} | ANZSCO {pr.get('anzsco','')} | {mltssl_tag}"
        )

    lines += ["", "--- Matched (already in your CV) ---"]
    if gap["matched_skills"]:
        lines += [f"  ✔  {s}" for s in gap["matched_skills"]]
    else:
        lines.append("  (none detected — use exact domain terminology)")

    lines += ["", "--- Missing (add these to strengthen your application) ---"]
    if gap["missing_skills"]:
        lines += [f"  ✘  {s}" for s in gap["missing_skills"]]
    else:
        lines.append("  (none — great coverage!)")

    lines += ["", "--- Recommendations ---"]
    lines += [f"  •  {r}" for r in gap["recommendations"]]

    job_kws = extract_keywords(
        f"{job.get('description','')} {job.get('requirements','')}", top_n=15
    )
    lines += ["", "--- High-value phrases from this job description ---"]
    lines += [f"  →  {kw}" for kw in job_kws[:10]]

    return "\n".join(lines)
