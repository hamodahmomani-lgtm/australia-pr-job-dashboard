"""
Cover letter generator — calibrated to Mohammad Almomani's PhD health-economics profile.

Templates are written from his background:
  - PhD Economics, Flinders University (2025)
  - 10 peer-reviewed publications (health economics, ageing, functional health)
  - Casual Academic at Adelaide University + Flinders University
  - Stata, Python, R, Power BI, SQL
  - SHARE / HILDA / ALSWH longitudinal survey expertise
  - IV, RDD, DiD, fixed-effects causal identification
  - GLO Affiliate Researcher
  - 4 years industry: energy market analyst, Qatar

Each template has a `{key_skill_1}` and `{key_skill_2}` slot filled from
CV-to-job keyword matching so every letter references skills the hiring
manager actually asked for.
"""

import re
import logging
from datetime import date
from config import CATEGORY_KEYWORDS, DEFAULT_PROFILE
from cv_match import get_matched_keywords, detect_category, extract_keywords

logger = logging.getLogger(__name__)


# ── Base layout ───────────────────────────────────────────────────────────────

_BASE = """
{today}

{hiring_manager}
{organization}
{location}

Dear {hiring_manager},

RE: Application for {job_title} — {organization}

{opening}

{body_1}

{body_2}

{closing_statement}

I have attached my curriculum vitae for your consideration. I welcome the opportunity to discuss how my background aligns with your team's needs. Please feel free to contact me at {email} or {phone}.

Yours sincerely,

{name}
{email} | {phone}
{linkedin}
""".strip()


# ── Category templates ────────────────────────────────────────────────────────
# Each value is a dict of paragraph keys matching the _BASE template slots.

TEMPLATES: dict[str, dict[str, str]] = {

    "Health Economist": {
        "opening": (
            "I am writing to apply for the {job_title} position at {organization}. "
            "With a PhD in Economics from Flinders University and a research programme "
            "centred on health economics, ageing, and functional health, I offer "
            "{organization} deep expertise in economic analysis of health outcomes "
            "and cost-effectiveness evaluation using large-scale longitudinal survey data."
        ),
        "body_1": (
            "My published work uses SHARE, HILDA, and ALSWH data to investigate how "
            "education, retirement policy, and locus of control shape functional "
            "independence and wellbeing in older adults — research directly relevant "
            "to health technology assessment and preventive health economics. "
            "I am proficient in {key_skill_1} and {key_skill_2}, and I apply "
            "causal identification strategies (IV, RDD, DiD, event study) to "
            "produce findings that robustly inform policy."
        ),
        "body_2": (
            "Alongside my research, I have {years_experience} years of applied "
            "experience across academic and industry settings, including energy "
            "market analysis at the enterprise level. I am fully conversant with "
            "the Australian health financing landscape, AIHW data infrastructure, "
            "and the evidence standards required for PBAC and health-policy submissions. "
            "I communicate technical findings clearly to non-specialist stakeholders "
            "and am comfortable working within APS or university environments."
        ),
        "closing_statement": (
            "I am deeply motivated by the opportunity to bring rigorous, "
            "evidence-based health economics to {organization}'s mission. "
            "I believe my combination of PhD-level econometric skills, "
            "a strong publication record, and practical research experience "
            "makes me an excellent fit for this role."
        ),
    },

    "Research Fellow": {
        "opening": (
            "I am delighted to submit my application for the {job_title} position "
            "at {organization}. As an early-career researcher with a completed PhD "
            "in Economics (Flinders University, 2025), ten peer-reviewed publications "
            "in leading journals, and an active research programme on ageing, health, "
            "and wellbeing, I am well positioned to contribute to {organization}'s "
            "research agenda."
        ),
        "body_1": (
            "My research uses the SHARE, HILDA, and ALSWH panel surveys — some of the "
            "richest longitudinal datasets for studying older adults — combined with "
            "rigorous causal methods including {key_skill_1} and {key_skill_2}. "
            "I have published in the Journal of Economic Studies, International "
            "Journal of Health Governance, Applied Economics, and Health Education, "
            "and I have presented at international conferences funded by NIA/NIH, "
            "the European Commission (SHARE-Gateway), and Netspar."
        ),
        "body_2": (
            "I have {years_experience} years of combined academic and industry "
            "experience, including current roles as Casual Academic at both Adelaide "
            "University and Flinders University and an affiliation with the Global "
            "Labor Organization (GLO). I am proficient in Stata, Python, R, and "
            "Power BI, and I have demonstrated capacity to deliver high-quality "
            "outputs under competitive-grant conditions. I am actively working on "
            "projects related to aged care, preventive health, and Indigenous "
            "wellbeing in Australia."
        ),
        "closing_statement": (
            "I am genuinely excited by the opportunity to deepen my research "
            "programme in collaboration with {organization}'s team. "
            "I am committed to translating rigorous academic work into policy-relevant "
            "insights and to contributing to a collegial, high-performing research culture."
        ),
    },

    "Lecturer": {
        "opening": (
            "I write to express my strong interest in the {job_title} position "
            "at {organization}. I am an early-career academic with a PhD in Economics "
            "(Flinders University, 2025), current teaching appointments at two "
            "Australian universities, and a commitment to student-centred, "
            "evidence-informed teaching in economics and applied data analysis."
        ),
        "body_1": (
            "I have designed and delivered units in {key_skill_1} and {key_skill_2} "
            "at both undergraduate and postgraduate levels. At Flinders University I "
            "coordinate units in Assessing Economic Environments, Coding for Business "
            "(Python), and Interpreting and Visualising Business Data. At Adelaide "
            "University I teach Digital Solution Methodologies and Introduction to "
            "Digital Disruption in Business. My teaching philosophy centres on "
            "real-world application, active learning, and building analytical "
            "literacy that students carry into professional roles."
        ),
        "body_2": (
            "My research into health economics and ageing directly enriches my "
            "teaching — I draw on live published findings to illustrate the "
            "practical value of econometric methods and data analysis. "
            "With {years_experience} years of academic experience, I have "
            "demonstrated the capacity to balance teaching, research, and "
            "publication output simultaneously. Earlier in my career I taught "
            "Mathematical Economics, Macroeconomics, and Microeconomics at "
            "Yarmouk University, Jordan."
        ),
        "closing_statement": (
            "I look forward to contributing to the academic culture at {organization}, "
            "to inspiring students through rigorous and engaging teaching, and to "
            "pursuing a collaborative research agenda in health economics and "
            "applied econometrics."
        ),
    },

    "Tutor": {
        "opening": (
            "I am applying for the {job_title} position at {organization}. "
            "I bring hands-on tutorial experience across economics, Python programming, "
            "and data analytics, and I am passionate about making quantitative "
            "concepts accessible and applicable to students at all levels."
        ),
        "body_1": (
            "As a Casual Academic at Adelaide University and Flinders University, "
            "I currently facilitate tutorials in {key_skill_1} and {key_skill_2}. "
            "I provide formative feedback, mark assessments, and adapt my delivery "
            "to diverse student cohorts — including domestic, international, and "
            "mature-age students — in both face-to-face and online modes."
        ),
        "body_2": (
            "My doctoral training in applied econometrics and health economics means "
            "I can contextualise tutorial content within current research and real-world "
            "applications, which consistently improves student engagement. "
            "I am comfortable with academic integrity procedures and committed "
            "to inclusive, respectful learning environments."
        ),
        "closing_statement": (
            "I would welcome the chance to support {organization}'s students and "
            "to contribute positively to the department's teaching community."
        ),
    },

    "Senior Policy Officer": {
        "opening": (
            "I am writing to apply for the {job_title} position at {organization}. "
            "With a PhD in Economics, a strong record of evidence-based research "
            "on health, ageing, and social policy, and substantial experience "
            "translating complex analysis into actionable policy recommendations, "
            "I offer {organization} the analytical depth and communication skills "
            "expected of a senior officer in the public sector."
        ),
        "body_1": (
            "My published research directly addresses the kinds of policy questions "
            "that state and federal governments prioritise — how retirement policy "
            "shapes functional health outcomes, how education investment reduces "
            "aged-care demand, and how preventive health expenditure affects "
            "long-term system costs. I am proficient in {key_skill_1} and "
            "{key_skill_2}, and I produce technically rigorous analysis that I "
            "routinely communicate to non-specialist audiences, including at "
            "ministerial-level forums and international research conferences. "
            "I understand the APS and state-government evidence culture and "
            "am experienced in drafting policy briefs, consultation documents, "
            "and strategic frameworks."
        ),
        "body_2": (
            "Over {years_experience} years spanning academic research, industry "
            "analysis, and university teaching, I have managed projects from "
            "conception to final report, worked across disciplinary boundaries, "
            "and delivered high-quality outputs under tight timelines. "
            "I am familiar with the datasets and analytical infrastructure most "
            "relevant to Australian government work — HILDA, ALSWH, AIHW "
            "administrative data — and I am comfortable engaging with regulatory "
            "frameworks, legislative context, and whole-of-government coordination. "
            "I classify at the APS EL1/EL2 level and have worked effectively "
            "in both collaborative team environments and as an independent researcher."
        ),
        "closing_statement": (
            "I am motivated by the opportunity to apply rigorous evidence-based "
            "analysis to policies that make a real difference for Australians. "
            "I look forward to bringing my commitment to policy excellence "
            "and stakeholder engagement to {organization}."
        ),
    },

    "Health Policy Officer": {
        "opening": (
            "I am writing to apply for the {job_title} at {organization}. "
            "With a PhD in Economics specialising in health economics and ageing, "
            "ten peer-reviewed publications on health outcomes and policy, "
            "and deep familiarity with Australia's health system — including "
            "AIHW datasets, Medicare, PBS, and aged care financing — I am "
            "well placed to contribute robust health policy analysis to {organization}."
        ),
        "body_1": (
            "My research programme sits squarely at the intersection of health "
            "economics and public policy. I have investigated how education and "
            "retirement policy shape functional health, wellbeing, and aged-care "
            "demand in older Australians; how preventive health interventions "
            "affect long-term health system costs; and how social determinants "
            "of health operate across the life course. I am proficient in "
            "{key_skill_1} and {key_skill_2}, and I apply cost-effectiveness "
            "analysis, HTA methodology, and causal-inference econometrics to "
            "generate findings that meet PBAC and AIHW evidence standards. "
            "I communicate technical health economics clearly to non-specialist "
            "policy and clinical stakeholders."
        ),
        "body_2": (
            "With {years_experience} years of combined research, teaching, and "
            "industry experience, I have a demonstrated track record of delivering "
            "analysis that bridges academic rigour and policy relevance. "
            "My involvement in Netspar, NIH/NIA-funded research networks, and the "
            "SHARE-Gateway collaboration has given me a broad perspective on "
            "international health and ageing policy that enriches my Australian "
            "work. I am currently affiliated with the Global Labor Organization "
            "and maintain an active publication pipeline on aged care, preventive "
            "health, and wellbeing economics."
        ),
        "closing_statement": (
            "I am deeply committed to evidence-driven health policy that improves "
            "outcomes for Australians — particularly in aged care, preventive "
            "health, and chronic disease. I would welcome the chance to discuss "
            "how my background aligns with {organization}'s health policy agenda."
        ),
    },

    "Program Evaluation Officer": {
        "opening": (
            "I am excited to apply for the {job_title} at {organization}. "
            "My PhD training in applied econometrics — specialising in causal "
            "identification strategies including instrumental variables, "
            "regression discontinuity, difference-in-differences, and event "
            "study designs — equips me with the rigorous methodological toolkit "
            "needed to design, conduct, and report program evaluations that "
            "deliver credible evidence for government decision-making."
        ),
        "body_1": (
            "I have applied these methods to evaluate the effects of retirement "
            "policy on functional health and aged-care demand, the causal impact "
            "of education on health outcomes across the life course, and the "
            "influence of household and community factors on child development. "
            "My expertise in {key_skill_1} and {key_skill_2} allows me to design "
            "evaluations that isolate program effects from confounders — a critical "
            "requirement for credible public program evaluation. I am comfortable "
            "working with logic models, theory of change frameworks, performance "
            "measurement systems, and mixed-methods designs, and I have reported "
            "evaluation findings to academic, government, and general-public audiences."
        ),
        "body_2": (
            "Across {years_experience} years in research and industry roles, "
            "I have combined strong technical skills (Stata, Python, R) with "
            "clear written and verbal communication. I have worked with large "
            "longitudinal datasets — SHARE, HILDA, ALSWH — that closely resemble "
            "the administrative and program data typical in government evaluation "
            "contexts. I am experienced in designing data collection instruments, "
            "managing multi-wave data cleaning, and producing reproducible "
            "analysis workflows. I am familiar with APS and state government "
            "evaluation frameworks and understand the accountability and reporting "
            "requirements of publicly funded program evaluations."
        ),
        "closing_statement": (
            "I am passionate about using high-quality evaluation evidence to "
            "drive genuine improvement in public programs and to ensure government "
            "investment delivers measurable outcomes for Australians. "
            "I look forward to contributing that commitment to {organization}."
        ),
    },

    "Policy Analyst": {
        "opening": (
            "I am writing to apply for the {job_title} role at {organization}. "
            "With a PhD in Economics, a track record of peer-reviewed research "
            "on health and social policy, and analytical skills in advanced "
            "causal-inference methods, I am well equipped to contribute "
            "high-quality, evidence-based policy analysis to {organization}."
        ),
        "body_1": (
            "My published research directly addresses policy questions: how "
            "retirement policy affects functional health; how education can "
            "reduce aged-care demand; and how household structure shapes "
            "child development outcomes. I am proficient in {key_skill_1} and "
            "{key_skill_2}, and I produce technically rigorous analysis that is "
            "clearly communicated to non-specialist audiences, including "
            "ministerial-level stakeholders."
        ),
        "body_2": (
            "With {years_experience} years of experience spanning academic "
            "research, industry analysis, and university teaching, I understand "
            "the evidence standards required in the APS environment and "
            "am comfortable working within the APS 5–EL1 classification range. "
            "I am familiar with AIHW data infrastructure, HILDA and ALSWH "
            "survey datasets, and the broader Australian health and social "
            "policy landscape."
        ),
        "closing_statement": (
            "I am committed to evidence-based governance and motivated by the "
            "opportunity to translate rigorous analysis into policies that "
            "improve outcomes for Australians. I look forward to bringing "
            "that commitment to {organization}."
        ),
    },

    "Evaluation Specialist": {
        "opening": (
            "I am excited to apply for the {job_title} at {organization}. "
            "My PhD training in applied econometrics and causal inference — "
            "including fixed effects, instrumental variables, regression "
            "discontinuity, and difference-in-differences designs — gives me "
            "a rigorous methodological toolkit for program and policy evaluation."
        ),
        "body_1": (
            "I have applied these methods to evaluate the effects of retirement "
            "policy on functional health, the impact of education on aged-care "
            "need, and the influence of household factors on child development. "
            "My expertise in {key_skill_1} and {key_skill_2} means I can design "
            "evaluations that isolate causal effects rather than merely describing "
            "correlational patterns — a critical distinction for policy-relevant "
            "findings."
        ),
        "body_2": (
            "With {years_experience} years of research and industry experience, "
            "I combine strong technical skills (Stata, Python, R) with clear "
            "written and verbal communication. I am experienced in working with "
            "large longitudinal datasets (SHARE, HILDA, ALSWH) and in translating "
            "complex evaluation findings for executive and ministerial audiences."
        ),
        "closing_statement": (
            "I am passionate about using rigorous evaluation evidence to drive "
            "continuous improvement in public programs, and I look forward to "
            "contributing that commitment to {organization}."
        ),
    },

    "Government Research Officer": {
        "opening": (
            "I am writing to apply for the {job_title} role at {organization}. "
            "As a PhD economist with a research programme centred on health, "
            "ageing, and social outcomes, and with expertise in the Australian "
            "longitudinal datasets most relevant to government research "
            "(HILDA, ALSWH, SHARE), I am well placed to contribute high-quality "
            "analysis to {organization}'s research and evidence function."
        ),
        "body_1": (
            "My published research addresses questions directly relevant to "
            "government policy — aged-care demand, retirement system design, "
            "preventive health, and Indigenous wellbeing. I am proficient in "
            "{key_skill_1} and {key_skill_2}, and I apply advanced "
            "causal-inference methods (IV, RDD, DiD, event study) to produce "
            "findings that robustly inform investment and policy decisions. "
            "I am familiar with AIHW data infrastructure and the evidence "
            "standards applied in the APS research context."
        ),
        "body_2": (
            "Across {years_experience} years in academic and industry roles, "
            "I have demonstrated the ability to manage research projects from "
            "inception to publication, communicate complex findings clearly, "
            "and collaborate across disciplinary boundaries. I am currently an "
            "Affiliate Researcher with the Global Labor Organization and a "
            "Casual Academic at Adelaide University and Flinders University, "
            "maintaining an active research output alongside teaching commitments."
        ),
        "closing_statement": (
            "I am drawn to {organization}'s mandate to generate independent, "
            "rigorous evidence for Australian decision-makers. I am confident "
            "my background in applied economics, my familiarity with Australian "
            "administrative and survey data, and my commitment to evidence-based "
            "policy make me an excellent fit for this role."
        ),
    },

    "Data Analyst": {
        "opening": (
            "I am applying for the {job_title} position at {organization}. "
            "As an applied economist and data analyst with hands-on experience "
            "in Stata, Python, R, Power BI, and SQL — and with a research "
            "career built on extracting causal insights from complex longitudinal "
            "datasets — I am confident in my ability to deliver rigorous, "
            "actionable analysis for {organization}."
        ),
        "body_1": (
            "My analytical work spans large panel surveys (SHARE, HILDA, ALSWH) "
            "and covers the full pipeline from data cleaning and transformation "
            "to statistical modelling and results communication. I have built "
            "visualisations and summary tables in Python and Power BI for both "
            "academic publications and internal reporting. My expertise in "
            "{key_skill_1} and {key_skill_2} means I approach data problems "
            "with both technical rigour and a clear research question."
        ),
        "body_2": (
            "Prior to my PhD, I spent approximately four years as an Economic "
            "and Energy Market Analyst at Mubadra Qatar, where I conducted "
            "data-driven market analysis under commercial deadlines. This "
            "industry experience complements my academic training and gives me "
            "practical appreciation for the communication and reporting standards "
            "required in an {organization} environment. With {years_experience} "
            "years of combined experience, I bring strong attention to data "
            "quality, reproducible workflows, and clear stakeholder reporting."
        ),
        "closing_statement": (
            "I am eager to apply my technical and analytical capabilities "
            "to {organization} and to help translate complex data into "
            "meaningful evidence that supports better outcomes."
        ),
    },

    "Business Intelligence Analyst": {
        "opening": (
            "I am writing to apply for the {job_title} at {organization}. "
            "With experience in Power BI dashboard development, SQL querying, "
            "and Python-based data pipelines — combined with {years_experience} "
            "years of analytical experience in both academic research and "
            "commercial energy markets — I am well placed to support "
            "{organization}'s BI and reporting function."
        ),
        "body_1": (
            "I specialise in {key_skill_1} and {key_skill_2}, and I have "
            "delivered end-to-end analytics solutions including interactive "
            "dashboards, automated reporting pipelines, and summary data "
            "products for executive audiences. During my time as an Economic "
            "and Energy Market Analyst at Mubadra Qatar, I produced regular "
            "market intelligence reports used for strategic investment decisions."
        ),
        "body_2": (
            "My PhD training in applied econometrics has refined my ability "
            "to extract meaningful signals from noisy data, validate analytical "
            "models, and communicate findings clearly. I bring experience with "
            "longitudinal datasets (HILDA, SHARE), Excel modelling, and "
            "statistical analysis in Python and Stata — skills that translate "
            "directly to BI work requiring rigorous, reproducible analysis."
        ),
        "closing_statement": (
            "I would welcome the opportunity to contribute my analytical and "
            "BI skills to {organization} and to help build a data culture "
            "that supports evidence-based strategic decisions."
        ),
    },

    "Economist": {
        "opening": (
            "I am writing to express my interest in the {job_title} role at "
            "{organization}. With a completed PhD in Economics (Flinders University, "
            "2025), ten published papers in peer-reviewed journals, and deep "
            "expertise in applied econometrics and causal inference, I am eager "
            "to contribute rigorous economic analysis to {organization}'s "
            "research and advisory work."
        ),
        "body_1": (
            "My work spans health economics, labour economics, and population "
            "economics, with a focus on {key_skill_1} and {key_skill_2}. "
            "I have a track record of delivering high-quality economic analysis "
            "under competitive conditions, and I am proficient in Stata, Python, "
            "R, Power BI, and SQL. I write clearly for both specialist and "
            "general-policy audiences, and I have presented findings at "
            "international conferences funded by NIA/NIH, the European Commission, "
            "and Netspar."
        ),
        "body_2": (
            "Over {years_experience} years I have combined academic research, "
            "university teaching, and commercial market analysis. I understand "
            "the Australian economic-policy environment, am familiar with AIHW "
            "and ABS datasets, and am motivated by work that improves public "
            "welfare through rigorous evidence. I am affiliated with the Global "
            "Labor Organization and maintain an active research pipeline on "
            "ageing, health, and wellbeing."
        ),
        "closing_statement": (
            "I am keen to apply my economic skills and policy instincts "
            "at {organization} and to be part of a team that makes a "
            "genuine difference in Australian economic policy outcomes."
        ),
    },
}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _safe(value: str | None, fallback: str) -> str:
    return (value or "").strip() or fallback


def _extract_years(profile: dict, cv_text: str) -> str:
    """
    Return a years-of-experience string.
    Strategy:
      1. profile['years_experience'] (int or '7')
      2. Regex in profile['experience'] text
      3. cv_parser.extract_years_experience(cv_text)
      4. Regex in raw cv_text
      5. DEFAULT_PROFILE fallback
      6. "several"
    """
    # Direct numeric field
    yrs = profile.get("years_experience")
    if yrs and str(yrs).strip().isdigit():
        return str(yrs).strip()

    exp_raw = (profile.get("experience") or "").strip()
    m = re.search(r"(\d{1,2})\s*\+?\s*year", exp_raw, re.IGNORECASE)
    if m:
        return m.group(1)

    if cv_text:
        try:
            from cv_parser import extract_years_experience
            years = extract_years_experience(cv_text)
            if years:
                return str(years)
        except ImportError:
            pass
        m2 = re.search(r"(\d{1,2})\s*\+?\s*year", cv_text, re.IGNORECASE)
        if m2:
            return m2.group(1)

    # Fall back to DEFAULT_PROFILE
    default_yrs = DEFAULT_PROFILE.get("years_experience")
    if default_yrs:
        return str(default_yrs)

    return "several"


def _pick_key_skills(job: dict, profile: dict, cv_text: str) -> tuple[str, str]:
    """
    Return (skill_1, skill_2) for the cover letter body.

    Priority:
      1. Keywords present in BOTH cv_text (or PROFILE_CV_TEXT fallback)
         AND job text — strongest signal that the role values what we have
      2. Category keywords present in job text
      3. High-value phrases from job text alone
    """
    from cv_match import PROFILE_CV_TEXT
    job_text = f"{job.get('description', '')} {job.get('requirements', '')}"
    category = job.get("category") or detect_category(job_text)

    # Use the uploaded CV if available, else fall back to profile anchor text
    effective_cv = cv_text.strip() or PROFILE_CV_TEXT

    matched = get_matched_keywords(effective_cv, job_text)
    if len(matched) >= 2:
        return matched[0], matched[1]
    if len(matched) == 1:
        job_kws = extract_keywords(job_text, top_n=10)
        second = next((k for k in job_kws if k != matched[0]), "economic analysis")
        return matched[0], second

    # Category keywords visible in job text
    cat_kws = CATEGORY_KEYWORDS.get(category, [])
    cat_in_job = [kw for kw in cat_kws if kw.lower() in job_text.lower()]
    if len(cat_in_job) >= 2:
        return cat_in_job[0], cat_in_job[1]
    if len(cat_in_job) == 1:
        job_kws = extract_keywords(job_text, top_n=10)
        second = next((k for k in job_kws if k != cat_in_job[0]), "policy analysis")
        return cat_in_job[0], second

    # Last resort — top job phrases
    job_kws = extract_keywords(job_text, top_n=10)
    k1 = job_kws[0] if job_kws else "applied econometrics"
    k2 = job_kws[1] if len(job_kws) > 1 else "health economics"
    return k1, k2


# ── Public API ────────────────────────────────────────────────────────────────

def generate_cover_letter(
    job: dict,
    profile: dict | None = None,
    cv_text: str = "",
    hiring_manager: str = "The Hiring Manager",
    extra_notes: str = "",
) -> str:
    """
    Merge a category template with job details and user profile.

    Falls back to DEFAULT_PROFILE for name/email/phone/LinkedIn
    so letters are always personalised even without a DB profile entry.
    """
    # Merge: DB profile overrides DEFAULT_PROFILE, explicit args override both
    merged = {**DEFAULT_PROFILE, **(profile or {})}

    category = job.get("category") or detect_category(
        f"{job.get('description', '')} {job.get('requirements', '')}"
    )
    template = TEMPLATES.get(category, TEMPLATES["Economist"])

    sal_min = job.get("salary_min") or 0
    sal_max = job.get("salary_max") or 0
    salary_range = f"${sal_min:,}–${sal_max:,}" if sal_min and sal_max else "competitive"

    skill_1, skill_2 = _pick_key_skills(job, merged, cv_text)

    context = {
        "today":           date.today().strftime("%d %B %Y"),
        "name":            _safe(merged.get("name"), "Mohammad Almomani"),
        "email":           _safe(merged.get("email"), "Mohammad.almomani@adelaide.edu.au"),
        "phone":           _safe(merged.get("phone"), "+61452608631"),
        "linkedin":        _safe(merged.get("linkedin"), "linkedin.com/in/mohammadalmomani"),
        "job_title":       job.get("title", "the advertised position"),
        "organization":    job.get("organization", "your organisation"),
        "location":        job.get("location", "Australia"),
        "hiring_manager":  hiring_manager,
        "salary_range":    salary_range,
        "employment_type": job.get("employment_type", "full-time"),
        "key_skill_1":     skill_1,
        "key_skill_2":     skill_2,
        "years_experience": _extract_years(merged, cv_text),
    }

    body_2_text = template["body_2"].format(**context)
    if extra_notes:
        body_2_text = f"{body_2_text}\n\n{extra_notes}"

    try:
        letter = _BASE.format(
            opening=template["opening"].format(**context),
            body_1=template["body_1"].format(**context),
            body_2=body_2_text,
            closing_statement=template["closing_statement"].format(**context),
            **context,
        )
    except KeyError as exc:
        logger.warning("Template key missing %s — rebuilding with format_map", exc)
        letter = _BASE.format(
            opening=template.get("opening", "").format_map(context),
            body_1=template.get("body_1", "").format_map(context),
            body_2=body_2_text.format_map(context),
            closing_statement=template.get("closing_statement", "").format_map(context),
            **context,
        )

    return letter


def generate_all_versions(
    job: dict,
    profile: dict | None = None,
    cv_text: str = "",
) -> dict[str, str]:
    """
    Return a standard and a brief version of the cover letter.

    Brief version keeps complete paragraphs within a 200-word budget
    then appends the sign-off block so the letter is always closeable.
    """
    standard = generate_cover_letter(job, profile, cv_text)

    paragraphs = [p.strip() for p in standard.split("\n\n") if p.strip()]

    SIGN_OFF_START = "I have attached my curriculum vitae"
    sign_off_idx = next(
        (i for i, p in enumerate(paragraphs) if p.startswith(SIGN_OFF_START)),
        len(paragraphs) - 2,
    )

    brief_paragraphs = []
    word_count = 0
    for i, para in enumerate(paragraphs):
        if i >= sign_off_idx:
            break
        words = len(para.split())
        if word_count + words > 180 and brief_paragraphs:
            break
        brief_paragraphs.append(para)
        word_count += words

    brief_paragraphs.extend(paragraphs[sign_off_idx:])
    brief = "\n\n".join(brief_paragraphs)

    return {"standard": standard, "brief": brief}
