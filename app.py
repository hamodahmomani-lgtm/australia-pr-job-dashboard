"""Australia PR Job Dashboard — main Streamlit application."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

from config import (
    JOB_CATEGORIES, JOB_SOURCES, APPLICATION_STATUSES,
    STATES, EMPLOYMENT_TYPES,
)
from database import (
    init_db, get_jobs, get_job, update_job_score,
    get_applications, save_application, update_application, delete_application,
    get_user_profile, save_user_profile,
    get_cover_letters, save_cover_letter,
    get_dashboard_stats, get_last_scrape, get_scrape_history,
)
from cv_match import score_jobs, get_skills_gap, tailor_cv_suggestions, detect_pr_relevance
from cover_letter import generate_cover_letter
from exporter import jobs_to_csv, applications_to_csv, export_filename

# ── Page config (must be first Streamlit call) ────────────────────────────────

st.set_page_config(
    page_title="Australia PR Job Dashboard",
    page_icon="🇦🇺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark theme CSS ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0d1b2a; }
    [data-testid="stSidebar"] * { color: #e0e0e0 !important; }
    [data-testid="stSidebarNav"] { display: none; }
    .stApp { background: #0a1628; color: #e0e0e0; }
    h1, h2, h3 { color: #90e0ef; }
    p, li, label { color: #c8d6e5; }

    .job-card {
        background: #1e2d3d;
        border-left: 4px solid #00b4d8;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .job-card h4 { margin: 0 0 4px; color: #90e0ef; }
    .job-card .meta { font-size: 0.82rem; color: #a0b0bf; }

    .score-high { color: #48cae4; font-weight: 700; }
    .score-mid  { color: #f4a261; font-weight: 700; }
    .score-low  { color: #e63946; font-weight: 700; }

    [data-testid="stMetric"] {
        background: #1e2d3d;
        border-radius: 10px;
        padding: 16px !important;
    }
    div.stButton > button {
        background: #023e8a; color: #e0f7fa;
        border: none; border-radius: 6px;
    }
    div.stButton > button:hover { background: #0077b6; color: #fff; }
    [data-testid="stExpander"] { background: #1e2d3d; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ── One-time initialisation ───────────────────────────────────────────────────

@st.cache_resource
def _init():
    """Run once per Streamlit process: initialise DB and start scheduler."""
    init_db()
    # Install Playwright's Chromium binary if it hasn't been installed yet.
    # Required on Streamlit Cloud which has no pre-install hook; safe no-op locally.
    try:
        import subprocess, sys
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=False, capture_output=True, timeout=120,
        )
    except Exception:
        pass
    try:
        from scheduler import start_scheduler
        start_scheduler()
    except Exception:
        pass
    return True


_init()


# ── Session state defaults ─────────────────────────────────────────────────────

if "cv_text" not in st.session_state:
    st.session_state.cv_text = get_user_profile().get("cv_text", "")
if "scored_jobs" not in st.session_state:
    st.session_state.scored_jobs = []


# ── Sidebar ────────────────────────────────────────────────────────────────────

PAGES = {
    "Dashboard":         "🏠 Dashboard",
    "Browse Jobs":       "🔍 Browse Jobs",
    "Applications":      "📋 Applications",
    "CV & Matching":     "🎯 CV & Matching",
    "Cover Letters":     "✍️ Cover Letters",
    "Settings":          "⚙️ Settings",
}

with st.sidebar:
    st.markdown("## 🇦🇺 PR Job Dashboard")
    st.markdown("---")
    page_key = st.radio(
        "Navigate",
        list(PAGES.keys()),
        format_func=lambda k: PAGES[k],
        label_visibility="collapsed",
    )
    st.markdown("---")

    _profile = get_user_profile()
    if _profile.get("name"):
        st.markdown(f"**{_profile['name']}**")
        st.caption(_profile.get("visa_status", ""))
    else:
        st.info("Complete your profile in Settings.")

    st.markdown("---")
    # ── Sidebar scraper controls
    st.markdown("**Job Refresh**")
    if st.button("🔄 Refresh All Now", use_container_width=True):
        with st.spinner("Scraping jobs…"):
            try:
                from scrapers.coordinator import run_all_scrapers
                summary = run_all_scrapers()
                st.success(
                    f"Done: {summary['total_new']} new / "
                    f"{summary['total_fetched']} fetched"
                )
            except Exception as exc:
                st.error(f"Scrape failed: {exc}")

    last = get_last_scrape()
    if last:
        st.caption(f"Last run: {(last.get('finished_at') or '')[:16]}")
        st.caption(f"New: {last.get('new_jobs',0)}")

    try:
        from scheduler import get_next_run_time, scheduler_running
        if scheduler_running():
            next_run = get_next_run_time()
            st.caption(f"Next: {next_run}" if next_run else "Scheduler running")
        else:
            st.caption("Scheduler inactive")
    except ImportError:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    st.title("Dashboard")
    stats = get_dashboard_stats()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Jobs", stats["total_jobs"])
    c2.metric("New This Week", stats["new_this_week"])
    c3.metric("Applications", stats["total_applications"])
    c4.metric("Active Pipeline", stats["active_applications"])

    left, right = st.columns(2)

    with left:
        st.subheader("Jobs by Category")
        if stats["by_category"]:
            fig = px.pie(
                names=list(stats["by_category"].keys()),
                values=list(stats["by_category"].values()),
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c8d6e5", legend=dict(font=dict(color="#c8d6e5")),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No job data yet.")

    with right:
        st.subheader("Application Pipeline")
        if stats["by_status"]:
            status_order = APPLICATION_STATUSES
            filtered_s = {s: stats["by_status"].get(s, 0) for s in status_order}
            fig2 = go.Figure(go.Bar(
                x=list(filtered_s.values()),
                y=list(filtered_s.keys()),
                orientation="h",
                marker_color="#0096c7",
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c8d6e5",
                xaxis=dict(gridcolor="#1e2d3d"), height=320,
                margin=dict(l=0, r=0, t=20, b=0),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No applications yet.")

    st.markdown("---")
    st.subheader("Recent Jobs")
    recent = get_jobs(limit=15)
    if recent:
        df_cols = ["title", "organization", "category", "location",
                   "salary_min", "salary_max", "posted_date", "closing_date"]
        df = pd.DataFrame(recent)[df_cols]
        df["Salary"] = df.apply(
            lambda r: f"${int(r.salary_min):,}–${int(r.salary_max):,}"
            if r.salary_min else "—", axis=1
        )
        df = df.drop(columns=["salary_min", "salary_max"])
        df.columns = ["Title", "Organisation", "Category", "Location",
                      "Posted", "Closing", "Salary"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Export All Jobs (CSV)",
            data=jobs_to_csv(get_jobs()),
            file_name=export_filename("jobs"),
            mime="text/csv",
        )
    else:
        st.info("No jobs loaded. Use the Refresh button in the sidebar.")

    # ── Scrape history
    st.markdown("---")
    st.subheader("Scrape History")
    history = get_scrape_history(limit=5)
    if history:
        df_h = pd.DataFrame(history)[["started_at", "finished_at", "new_jobs",
                                       "total_fetched"]]
        df_h.columns = ["Started", "Finished", "New Jobs", "Total Fetched"]
        st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.caption("No scrape runs recorded yet.")


# ══════════════════════════════════════════════════════════════════════════════
# BROWSE JOBS
# ══════════════════════════════════════════════════════════════════════════════

def page_browse_jobs():
    st.title("Browse Jobs")

    with st.expander("Filters", expanded=True):
        fc1, fc2, fc3, fc4 = st.columns(4)
        cat_filter   = fc1.selectbox("Category", ["All"] + JOB_CATEGORIES)
        src_filter   = fc2.selectbox("Source",   ["All"] + JOB_SOURCES)
        state_filter = fc3.selectbox("State",    ["All"] + STATES)
        keyword      = fc4.text_input("Keyword")
        sal_min      = st.slider("Min salary ($)", 0, 200_000, 0, step=5_000)
        sort_by      = st.radio("Sort by", ["Newest", "Match Score", "Salary"],
                                 horizontal=True)

    jobs = get_jobs(
        category=cat_filter if cat_filter != "All" else None,
        source=src_filter if src_filter != "All" else None,
        state=state_filter if state_filter != "All" else None,
        keyword=keyword or None,
        min_salary=sal_min,
    )

    cv = st.session_state.cv_text
    if cv and jobs:
        jobs = score_jobs(cv, jobs)
        for j in jobs:
            if j.get("id"):
                update_job_score(j["id"], j["match_score"])

    if sort_by == "Match Score":
        jobs = sorted(jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    elif sort_by == "Salary":
        jobs = sorted(jobs, key=lambda x: x.get("salary_min") or 0, reverse=True)

    hdr_col, exp_col = st.columns([3, 1])
    hdr_col.markdown(f"**{len(jobs)} job(s)**")
    exp_col.download_button(
        "⬇️ Export (CSV)",
        data=jobs_to_csv(jobs),
        file_name=export_filename("jobs_filtered"),
        mime="text/csv",
    )

    for job in jobs:
        score = job.get("match_score", 0)
        score_cls = "score-high" if score >= 65 else ("score-mid" if score >= 40 else "score-low")
        score_str = f'<span class="{score_cls}">{score:.0f}%</span>' if score else "—"
        sal_str = (
            f"${job['salary_min']:,}–${job['salary_max']:,}"
            if job.get("salary_min") else "Not specified"
        )

        # PR-eligibility badge
        pr = detect_pr_relevance(job)
        if pr.get("mltssl"):
            pr_badge = '🟢 <b>MLTSSL</b>'
        elif pr.get("pr_eligible"):
            pr_badge = '🟡 PR-eligible'
        else:
            pr_badge = '🔴 Not PR-eligible'

        st.markdown(f"""
<div class="job-card">
  <h4>{job['title']}</h4>
  <div class="meta">
    🏢 {job['organization']} &nbsp;|&nbsp;
    📍 {job['location'] or '—'} &nbsp;|&nbsp;
    🏷️ {job['category']} &nbsp;|&nbsp;
    🌐 {job['source']}<br>
    💰 {sal_str} &nbsp;|&nbsp;
    📅 {job['posted_date']} &nbsp;|&nbsp;
    ⏳ Closes {job['closing_date'] or '—'} &nbsp;|&nbsp;
    Match: {score_str} &nbsp;|&nbsp; {pr_badge}
  </div>
</div>
""", unsafe_allow_html=True)

        with st.expander("Details & Actions"):
            tab_desc, tab_req, tab_act = st.tabs(["Description", "Requirements", "Actions"])

            with tab_desc:
                st.write(job.get("description") or "No description available.")
            with tab_req:
                st.write(job.get("requirements") or "No requirements listed.")
            with tab_act:
                ac1, ac2, ac3, ac4 = st.columns(4)
                if ac1.button("📌 Bookmark", key=f"bm_{job['id']}"):
                    save_application(job["id"], "Bookmarked")
                    st.success("Bookmarked!")
                if ac2.button("📤 Mark Applied", key=f"ap_{job['id']}"):
                    app_id = save_application(job["id"], "Applied")
                    update_application(
                        app_id,
                        status="Applied",
                        applied_date=date.today().isoformat(),
                    )
                    st.success("Marked as applied!")
                if job.get("url"):
                    ac3.link_button("🔗 Open Listing", job["url"])
                if cv:
                    if ac4.button("✍️ Cover Letter", key=f"cl_{job['id']}"):
                        profile = get_user_profile()
                        letter = generate_cover_letter(job, profile, cv)
                        save_cover_letter(job["id"], letter)
                        st.success("Cover letter generated and saved!")

            if cv:
                gap = get_skills_gap(cv, job)
                st.markdown(
                    f"**CV Match:** {gap['score']:.0f}/100 &nbsp;|&nbsp;"
                    f"Skill coverage: {gap['coverage_pct']}%"
                )
                if gap["matched_skills"]:
                    st.success("Matched: " + " • ".join(gap["matched_skills"][:5]))
                if gap["missing_skills"]:
                    st.warning("Missing from CV: " + " • ".join(gap["missing_skills"][:5]))


# ══════════════════════════════════════════════════════════════════════════════
# APPLICATIONS TRACKER
# ══════════════════════════════════════════════════════════════════════════════

def page_applications():
    st.title("Application Tracker")

    apps = get_applications()

    if not apps:
        st.info("No applications yet. Bookmark a job from Browse Jobs.")
        return

    # Status summary row
    by_status: dict[str, int] = {}
    for a in apps:
        by_status[a["status"]] = by_status.get(a["status"], 0) + 1
    cols = st.columns(max(len(by_status), 1))
    for i, (s, cnt) in enumerate(by_status.items()):
        cols[i].metric(s, cnt)

    st.markdown("---")

    # ── Export
    dl_col, flt_col = st.columns([1, 3])
    dl_col.download_button(
        "⬇️ Export Applications (CSV)",
        data=applications_to_csv(apps),
        file_name=export_filename("applications"),
        mime="text/csv",
    )

    status_filter = flt_col.selectbox("Filter by status", ["All"] + APPLICATION_STATUSES)
    filtered = [a for a in apps if status_filter == "All" or a["status"] == status_filter]

    # ── Table view
    rows = []
    for a in filtered:
        rows.append({
            "ID": a["id"],
            "Title": a["title"],
            "Organisation": a["organization"],
            "Category": a["category"],
            "Status": a["status"],
            "Applied": a.get("applied_date") or "—",
            "Follow-up": a.get("follow_up_date") or "—",
            "Notes": (a.get("notes") or "")[:60],
        })
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df.drop(columns=["ID"]), use_container_width=True, hide_index=True)

    # ── Edit panel
    st.markdown("---")
    st.subheader("Update Application")
    options = {f"{r['Title']} @ {r['Organisation']} (#{r['ID']})": r["ID"] for r in rows}
    if not options:
        st.info("No applications match the current filter.")
        return

    selected_label = st.selectbox("Select", list(options.keys()))
    app_id = options[selected_label]
    app = next((a for a in apps if a["id"] == app_id), None)
    if not app:
        return

    with st.form(f"update_app_{app_id}"):
        u1, u2 = st.columns(2)
        new_status = u1.selectbox(
            "Status", APPLICATION_STATUSES,
            index=APPLICATION_STATUSES.index(app["status"])
            if app["status"] in APPLICATION_STATUSES else 0,
        )
        applied_dt = u2.date_input(
            "Applied date",
            value=date.fromisoformat(app["applied_date"])
            if app.get("applied_date") else date.today(),
        )
        followup_dt = u1.date_input(
            "Follow-up date",
            value=date.fromisoformat(app["follow_up_date"])
            if app.get("follow_up_date") else date.today(),
        )
        response_dt = u2.date_input(
            "Response date",
            value=date.fromisoformat(app["response_date"])
            if app.get("response_date") else date.today(),
        )
        notes = st.text_area("Notes", value=app.get("notes") or "")
        btn_save, btn_del = st.columns(2)
        save_pressed = btn_save.form_submit_button("💾 Save")
        del_pressed  = btn_del.form_submit_button("🗑️ Delete")

    if save_pressed:
        update_application(
            app_id,
            status=new_status,
            applied_date=applied_dt.isoformat(),
            follow_up_date=followup_dt.isoformat(),
            response_date=response_dt.isoformat(),
            notes=notes,
        )
        st.success("Updated!")
        st.rerun()
    if del_pressed:
        delete_application(app_id)
        st.warning("Application removed.")
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CV & MATCHING
# ══════════════════════════════════════════════════════════════════════════════

def page_cv_matching():
    st.title("CV & Matching")

    # ── Upload or paste CV
    upload_tab, paste_tab = st.tabs(["Upload CV (PDF/DOCX/TXT)", "Paste CV Text"])

    with upload_tab:
        uploaded = st.file_uploader(
            "Upload your CV",
            type=["pdf", "docx", "doc", "txt"],
            help="PDF and DOCX are parsed automatically. TXT is used as-is.",
        )
        if uploaded:
            try:
                from cv_parser import parse_uploaded_file
                parsed = parse_uploaded_file(uploaded)
                if parsed:
                    st.session_state.cv_text = parsed
                    st.success(f"Parsed {len(parsed)} characters from {uploaded.name}.")
                else:
                    st.error("Could not extract text from the uploaded file.")
            except ImportError:
                # cv_parser uses optional dependencies; fall back gracefully
                text = uploaded.read()
                if uploaded.name.endswith(".txt"):
                    st.session_state.cv_text = text.decode("utf-8", errors="replace")
                    st.success("Loaded text file.")
                else:
                    st.warning(
                        "Install pymupdf and python-docx to parse PDF/DOCX: "
                        "`pip install pymupdf python-docx`"
                    )

    with paste_tab:
        pasted = st.text_area(
            "Paste CV text",
            value=st.session_state.cv_text,
            height=300,
            placeholder="Paste the plain text of your CV here…",
        )
        if st.button("Use pasted text"):
            st.session_state.cv_text = pasted
            st.success("CV text updated.")

    cv = st.session_state.cv_text
    if not cv:
        st.info("Upload or paste your CV above to enable scoring.")
        return

    st.markdown(f"**CV loaded:** {len(cv.split())} words")

    col_score, col_save = st.columns(2)
    run_scoring = col_score.button("Score all jobs", use_container_width=True)
    save_cv = col_save.button("Save CV to profile", use_container_width=True)

    if save_cv:
        profile = get_user_profile()
        profile["cv_text"] = cv
        save_user_profile(profile)
        st.success("CV saved to profile.")

    if run_scoring:
        with st.spinner("Scoring…"):
            all_jobs = get_jobs()
            scored = score_jobs(cv, all_jobs)
            for j in scored:
                if j.get("id"):
                    update_job_score(j["id"], j["match_score"])
            st.session_state.scored_jobs = scored
        st.success(f"Scored {len(scored)} jobs.")

    if st.session_state.scored_jobs:
        scored = st.session_state.scored_jobs
        top = sorted(scored, key=lambda x: x.get("match_score", 0), reverse=True)[:15]

        st.subheader("Top 15 Matches")
        labels = [
            (j["title"][:40] + "…" if len(j["title"]) > 40 else j["title"])
            for j in top
        ]
        fig = px.bar(
            x=[j["match_score"] for j in top],
            y=labels,
            orientation="h",
            color=[j["match_score"] for j in top],
            color_continuous_scale="Blues",
            range_color=[0, 100],
            labels={"x": "Match Score", "y": ""},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c8d6e5", coloraxis_showscale=False,
            height=420, margin=dict(l=0, r=0, t=20, b=0),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Detailed gap for one job
        st.subheader("Skills Gap Detail")
        sel = st.selectbox(
            "Choose job for gap analysis",
            [f"{j['title']} @ {j['organization']}" for j in top],
        )
        idx = [f"{j['title']} @ {j['organization']}" for j in top].index(sel)
        chosen = top[idx]
        gap = get_skills_gap(cv, chosen)

        g1, g2, g3 = st.columns(3)
        g1.metric("Match Score", f"{gap['score']:.0f} / 100")
        g2.metric("Skill Coverage", f"{gap['coverage_pct']}%")
        g3.metric("Missing Skills", len(gap["missing_skills"]))

        if gap["matched_skills"]:
            st.success("Matched: " + " · ".join(gap["matched_skills"]))
        if gap["missing_skills"]:
            st.warning("Missing: " + " · ".join(gap["missing_skills"]))
        for rec in gap["recommendations"]:
            st.info(f"💡 {rec}")

        with st.expander("Full tailoring suggestions"):
            st.code(tailor_cv_suggestions(cv, chosen), language=None)


# ══════════════════════════════════════════════════════════════════════════════
# COVER LETTERS
# ══════════════════════════════════════════════════════════════════════════════

def page_cover_letters():
    st.title("Cover Letters")

    jobs = get_jobs()
    if not jobs:
        st.info("No jobs found. Refresh jobs first.")
        return

    profile = get_user_profile()
    cv = st.session_state.cv_text

    job_labels = [f"{j['title']} @ {j['organization']}" for j in jobs]
    sel = st.selectbox("Select job", job_labels)
    job = jobs[job_labels.index(sel)]

    with st.expander("Job details"):
        st.markdown(f"**{job['title']}** — {job['organization']}")
        st.write(job.get("description") or "No description.")

    hiring_manager = st.text_input("Hiring manager", value="The Hiring Manager")
    extra_notes = st.text_area(
        "Personalisation / extra notes",
        height=80,
        placeholder="e.g. Mention a specific project or how you found the role.",
    )

    if cv:
        st.caption(f"Skills will be drawn from your uploaded CV ({len(cv.split())} words).")

    if st.button("Generate Cover Letter", use_container_width=True):
        with st.spinner("Generating…"):
            letter = generate_cover_letter(
                job, profile, cv_text=cv,
                hiring_manager=hiring_manager,
                extra_notes=extra_notes,
            )
            st.session_state.generated_letter = letter
            st.session_state.cl_job_id = job["id"]
            st.session_state.cl_job_title = job["title"]

    if "generated_letter" in st.session_state:
        st.markdown("---")
        edited = st.text_area(
            "Edit cover letter",
            value=st.session_state.generated_letter,
            height=520,
        )
        s_col, d_col = st.columns(2)
        if s_col.button("Save to library"):
            save_cover_letter(st.session_state.cl_job_id, edited)
            st.success("Saved!")
        d_col.download_button(
            "Download as .txt",
            data=edited,
            file_name=f"cover_letter_{st.session_state.cl_job_title.replace(' ','_')}.txt",
            mime="text/plain",
        )

    # ── Library
    st.markdown("---")
    st.subheader("Saved Letters")
    saved = get_cover_letters()
    if saved:
        for cl in saved:
            label = (
                f"v{cl['version']} — "
                f"{cl.get('title') or 'Unknown'} @ {cl.get('organization') or ''}"
                f"  ({str(cl.get('created_at',''))[:10]})"
            )
            with st.expander(label):
                st.text(cl["content"])
                st.download_button(
                    "Download",
                    data=cl["content"],
                    file_name=f"cl_v{cl['version']}.txt",
                    mime="text/plain",
                    key=f"dl_cl_{cl['id']}",
                )
    else:
        st.info("No saved cover letters yet.")


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

def page_settings():
    st.title("Settings")

    tab_profile, tab_telegram, tab_scrapers = st.tabs(
        ["Profile", "Telegram Notifications", "Scrapers & Schedule"]
    )

    # ── Profile tab
    with tab_profile:
        profile = get_user_profile()
        with st.form("profile_form"):
            st.subheader("Personal Details")
            c1, c2 = st.columns(2)
            name     = c1.text_input("Full Name",   value=profile.get("name") or "")
            email    = c2.text_input("Email",        value=profile.get("email") or "")
            phone    = c1.text_input("Phone",        value=profile.get("phone") or "")
            linkedin = c2.text_input("LinkedIn URL", value=profile.get("linkedin") or "")

            visa_opts = [
                "Skilled Independent (189)", "Skilled Nominated (190)",
                "Employer Sponsored (482)", "Graduate (485)",
                "Permanent Resident", "Australian Citizen", "Other",
            ]
            visa_status = st.selectbox(
                "Visa / Work Rights", visa_opts,
                index=visa_opts.index(profile.get("visa_status", visa_opts[0]))
                if profile.get("visa_status") in visa_opts else 0,
            )
            target_roles = st.multiselect(
                "Target Job Categories", JOB_CATEGORIES,
                default=[r for r in (profile.get("target_roles") or "").split(",") if r],
            )

            st.subheader("Professional Background")
            experience = st.text_area(
                "Experience (start with number of years, e.g. '7 years…')",
                value=profile.get("experience") or "", height=80,
            )
            education = st.text_area("Education", value=profile.get("education") or "", height=80)
            skills    = st.text_area("Key Skills (comma-separated)",
                                      value=profile.get("skills") or "", height=80)

            cv_text_field = st.text_area(
                "CV Text (paste here or upload in CV & Matching)",
                value=profile.get("cv_text") or st.session_state.cv_text,
                height=250,
            )

            if st.form_submit_button("Save Profile", use_container_width=True):
                save_user_profile({
                    "name": name, "email": email, "phone": phone,
                    "linkedin": linkedin, "visa_status": visa_status,
                    "target_roles": ",".join(target_roles),
                    "experience": experience, "education": education,
                    "skills": skills, "cv_text": cv_text_field,
                })
                st.session_state.cv_text = cv_text_field
                st.success("Profile saved!")
                st.rerun()

    # ── Telegram tab
    with tab_telegram:
        st.subheader("Telegram Bot Notifications")
        st.markdown("""
To receive job alerts on Telegram:
1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token.
2. Message your bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates`
   to find your Chat ID.
3. Enter both values below — they are stored only in your `.env` file.
""")

        try:
            from notifier import is_configured, send_test_message
            configured = is_configured()
        except ImportError:
            configured = False

        if configured:
            st.success("Telegram is configured.")
        else:
            st.warning("Telegram not configured. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to your .env file.")

        st.markdown("**Manual configuration (`.env` file)**")
        st.code(
            "TELEGRAM_BOT_TOKEN=123456789:ABCDefGhijKlmNopQrsTUvWxyz\n"
            "TELEGRAM_CHAT_ID=987654321",
            language="bash",
        )

        if configured:
            if st.button("Send test message"):
                ok = send_test_message()
                if ok:
                    st.success("Test message sent!")
                else:
                    st.error("Failed — check your token and chat ID in .env.")

    # ── Scrapers & Schedule tab
    with tab_scrapers:
        st.subheader("Scheduler Status")
        try:
            from scheduler import scheduler_running, get_next_run_time, start_scheduler
            from config import SCRAPE_HOUR, SCRAPE_MINUTE
            if scheduler_running():
                st.success(f"Running — next scrape at {get_next_run_time()}")
            else:
                st.warning("Scheduler not running.")
                if st.button("Start scheduler"):
                    ok = start_scheduler()
                    st.success("Started!" if ok else "APScheduler not installed.")
            st.caption(f"Configured time: {SCRAPE_HOUR:02d}:{SCRAPE_MINUTE:02d} AEST "
                       f"(set SCRAPE_HOUR and SCRAPE_MINUTE in .env)")
        except ImportError:
            st.warning("APScheduler not installed: `pip install apscheduler`")

        st.markdown("---")
        st.subheader("Run Individual Scrapers")
        scraper_names = [
            "pageup", "seek", "aps_jobs", "deloitte", "kpmg", "pwc", "ey",
            "government", "csiro",
        ]
        sel_scraper = st.selectbox("Scraper", scraper_names)
        if st.button(f"Run {sel_scraper} now"):
            with st.spinner(f"Running {sel_scraper}…"):
                try:
                    from scrapers.coordinator import run_scraper
                    result = run_scraper(sel_scraper, keywords=None)
                    st.success(
                        f"Done: {result.get('new',0)} new / "
                        f"{result.get('total',0)} fetched"
                    )
                except Exception as exc:
                    st.error(f"Error: {exc}")

        st.markdown("---")
        st.subheader("Scrape History")
        history = get_scrape_history(limit=10)
        if history:
            df_h = pd.DataFrame(history)[
                ["started_at", "finished_at", "new_jobs", "total_fetched", "details"]
            ]
            df_h.columns = ["Started", "Finished", "New Jobs", "Total Fetched", "Details"]
            st.dataframe(df_h, use_container_width=True, hide_index=True)
        else:
            st.info("No scrape runs recorded.")

        st.markdown("---")
        st.subheader("Data Maintenance")
        if st.button("Delete jobs older than 90 days (no applications)"):
            from database import delete_old_jobs
            n = delete_old_jobs(90)
            st.success(f"Removed {n} old job(s).")


# ══════════════════════════════════════════════════════════════════════════════
# Router — dict dispatch (not substring matching)
# ══════════════════════════════════════════════════════════════════════════════

_PAGE_HANDLERS = {
    "Dashboard":     page_dashboard,
    "Browse Jobs":   page_browse_jobs,
    "Applications":  page_applications,
    "CV & Matching": page_cv_matching,
    "Cover Letters": page_cover_letters,
    "Settings":      page_settings,
}

_PAGE_HANDLERS[page_key]()
