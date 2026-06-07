"""
SQLite database layer.

Changes from v1:
  - Indexes on category, source, state, posted_date, match_score
  - scrape_log table
  - UNIQUE key changed to (title, organization, url) — not posted_date
    (posted_date shifts daily, making the old key useless for deduplication)
  - save_job returns the existing row id on conflict instead of 0
  - Explicit rollback on save_job exception
  - save_user_profile does not mutate the caller's dict
  - No private functions exposed outside this module
"""

import sqlite3
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # better concurrent read performance
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            organization    TEXT NOT NULL,
            location        TEXT,
            state           TEXT,
            category        TEXT,
            source          TEXT,
            salary_min      INTEGER,
            salary_max      INTEGER,
            description     TEXT,
            requirements    TEXT,
            url             TEXT,
            posted_date     TEXT,
            closing_date    TEXT,
            employment_type TEXT,
            is_pr_relevant  INTEGER DEFAULT 1,
            match_score     REAL    DEFAULT 0.0,
            created_at      TEXT    DEFAULT (datetime('now','localtime')),
            UNIQUE(title, organization, url)
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_category    ON jobs(category);
        CREATE INDEX IF NOT EXISTS idx_jobs_source      ON jobs(source);
        CREATE INDEX IF NOT EXISTS idx_jobs_state       ON jobs(state);
        CREATE INDEX IF NOT EXISTS idx_jobs_posted      ON jobs(posted_date DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_match       ON jobs(match_score DESC);

        CREATE TABLE IF NOT EXISTS applications (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id           INTEGER NOT NULL,
            status           TEXT    DEFAULT 'Bookmarked',
            applied_date     TEXT,
            notes            TEXT,
            cover_letter_id  INTEGER,
            follow_up_date   TEXT,
            response_date    TEXT,
            created_at       TEXT DEFAULT (datetime('now','localtime')),
            updated_at       TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
        CREATE INDEX IF NOT EXISTS idx_apps_status   ON applications(status);
        CREATE INDEX IF NOT EXISTS idx_apps_followup ON applications(follow_up_date);

        CREATE TABLE IF NOT EXISTS user_profile (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT,
            email        TEXT,
            phone        TEXT,
            linkedin     TEXT,
            cv_text      TEXT,
            skills       TEXT,
            experience   TEXT,
            education    TEXT,
            visa_status  TEXT DEFAULT 'Skilled Independent (189)',
            target_roles TEXT,
            created_at   TEXT DEFAULT (datetime('now','localtime')),
            updated_at   TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS cover_letters (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id         INTEGER,
            application_id INTEGER,
            content        TEXT,
            version        INTEGER DEFAULT 1,
            created_at     TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (job_id)         REFERENCES jobs(id),
            FOREIGN KEY (application_id) REFERENCES applications(id)
        );

        CREATE TABLE IF NOT EXISTS scrape_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at    TEXT,
            finished_at   TEXT,
            new_jobs      INTEGER DEFAULT 0,
            total_fetched INTEGER DEFAULT 0,
            details       TEXT,
            created_at    TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)

    seeded = cur.execute("SELECT value FROM meta WHERE key='seeded'").fetchone()
    if not seeded:
        _seed_sample_jobs(cur)
        cur.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('seeded','1')")

    profile_seeded = cur.execute(
        "SELECT value FROM meta WHERE key='profile_seeded'"
    ).fetchone()
    if not profile_seeded:
        _seed_default_profile(cur)
        cur.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('profile_seeded','1')")

    conn.commit()
    conn.close()


# ── Jobs ──────────────────────────────────────────────────────────────────────

def get_jobs(
    category: str | None = None,
    source: str | None = None,
    state: str | None = None,
    keyword: str | None = None,
    min_salary: int = 0,
    limit: int = 500,
) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM jobs WHERE 1=1"
    params: list = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if source:
        query += " AND source = ?"
        params.append(source)
    if state:
        query += " AND state = ?"
        params.append(state)
    if keyword:
        query += " AND (title LIKE ? OR organization LIKE ? OR description LIKE ?)"
        kw = f"%{keyword}%"
        params += [kw, kw, kw]
    if min_salary:
        query += " AND salary_min >= ?"
        params.append(min_salary)
    query += " ORDER BY posted_date DESC, id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_job(job: dict) -> tuple[int, bool]:
    """
    Insert a job; on UNIQUE conflict update description/salary if empty.
    Returns (row_id, is_new).  is_new is True only when a new row was inserted.
    Returns (0, False) on unexpected error.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO jobs
              (title,organization,location,state,category,source,
               salary_min,salary_max,description,requirements,url,
               posted_date,closing_date,employment_type,is_pr_relevant)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(title,organization,url) DO UPDATE SET
              description = CASE WHEN excluded.description != '' AND description = ''
                                 THEN excluded.description ELSE description END,
              salary_min  = CASE WHEN excluded.salary_min > 0 AND salary_min = 0
                                 THEN excluded.salary_min ELSE salary_min END,
              salary_max  = CASE WHEN excluded.salary_max > 0 AND salary_max = 0
                                 THEN excluded.salary_max ELSE salary_max END,
              closing_date = CASE WHEN excluded.closing_date != '' AND closing_date = ''
                                  THEN excluded.closing_date ELSE closing_date END
        """, (
            job.get("title", ""), job.get("organization", ""), job.get("location", ""),
            job.get("state", ""), job.get("category", ""), job.get("source", ""),
            job.get("salary_min", 0) or 0, job.get("salary_max", 0) or 0,
            job.get("description", ""), job.get("requirements", ""),
            job.get("url", ""), job.get("posted_date", ""), job.get("closing_date", ""),
            job.get("employment_type", "Full-time"), job.get("is_pr_relevant", 1),
        ))
        conn.commit()
        # SQLite sets lastrowid to the new row id on INSERT, 0 on DO UPDATE
        if cur.lastrowid:
            return cur.lastrowid, True
        # Conflict — retrieve the existing row id
        row = conn.execute(
            "SELECT id FROM jobs WHERE title=? AND organization=? AND url=?",
            (job.get("title", ""), job.get("organization", ""), job.get("url", "")),
        ).fetchone()
        return (row["id"] if row else 0), False
    except Exception as exc:
        conn.rollback()
        logger.error("save_job failed for '%s': %s", job.get("title"), exc)
        return 0, False
    finally:
        conn.close()


def update_job_score(job_id: int, score: float) -> None:
    conn = get_connection()
    conn.execute("UPDATE jobs SET match_score=? WHERE id=?", (round(score, 1), job_id))
    conn.commit()
    conn.close()


def get_job(job_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_old_jobs(days: int = 90) -> int:
    """Delete jobs older than `days` days that have no applications."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM jobs
        WHERE posted_date < date('now', ?)
          AND id NOT IN (SELECT DISTINCT job_id FROM applications)
    """, (f"-{days} days",))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


# ── Applications ──────────────────────────────────────────────────────────────

def get_applications() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.*, j.title, j.organization, j.category, j.location,
               j.salary_min, j.salary_max, j.url as job_url, j.closing_date as job_closing
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        ORDER BY a.updated_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_application(job_id: int, status: str = "Bookmarked", notes: str = "") -> int:
    conn = get_connection()
    cur = conn.cursor()
    existing = cur.execute(
        "SELECT id FROM applications WHERE job_id=?", (job_id,)
    ).fetchone()
    if existing:
        conn.close()
        return existing["id"]
    cur.execute(
        "INSERT INTO applications(job_id,status,notes) VALUES (?,?,?)",
        (job_id, status, notes),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_application(app_id: int, **kwargs) -> None:
    if not kwargs:
        return
    # Whitelist allowed columns to prevent accidental SQL issues
    _ALLOWED = {
        "status", "applied_date", "notes", "cover_letter_id",
        "follow_up_date", "response_date", "updated_at",
    }
    safe = {k: v for k, v in kwargs.items() if k in _ALLOWED}
    safe["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not safe:
        return
    cols = ", ".join(f"{k}=?" for k in safe)
    vals = list(safe.values()) + [app_id]
    conn = get_connection()
    conn.execute(f"UPDATE applications SET {cols} WHERE id=?", vals)
    conn.commit()
    conn.close()


def delete_application(app_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM applications WHERE id=?", (app_id,))
    conn.commit()
    conn.close()


# ── User Profile ──────────────────────────────────────────────────────────────

def get_user_profile() -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM user_profile ORDER BY id LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else {}


def save_user_profile(profile: dict) -> None:
    # Never mutate caller's dict
    data = dict(profile)
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    existing = conn.execute("SELECT id FROM user_profile LIMIT 1").fetchone()
    if existing:
        cols = ", ".join(f"{k}=?" for k in data)
        vals = list(data.values()) + [existing["id"]]
        conn.execute(f"UPDATE user_profile SET {cols} WHERE id=?", vals)
    else:
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        conn.execute(
            f"INSERT INTO user_profile({cols}) VALUES({placeholders})",
            list(data.values()),
        )
    conn.commit()
    conn.close()


# ── Cover Letters ─────────────────────────────────────────────────────────────

def get_cover_letters(job_id: int | None = None) -> list[dict]:
    conn = get_connection()
    if job_id:
        rows = conn.execute(
            "SELECT * FROM cover_letters WHERE job_id=? ORDER BY version DESC",
            (job_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT cl.*, j.title, j.organization "
            "FROM cover_letters cl LEFT JOIN jobs j ON cl.job_id=j.id "
            "ORDER BY cl.created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_cover_letter(job_id: int, content: str, application_id: int | None = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    existing = cur.execute(
        "SELECT MAX(version) as v FROM cover_letters WHERE job_id=?", (job_id,)
    ).fetchone()
    version = (existing["v"] or 0) + 1
    cur.execute(
        "INSERT INTO cover_letters(job_id,application_id,content,version) VALUES(?,?,?,?)",
        (job_id, application_id, content, version),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


# ── Scrape log ────────────────────────────────────────────────────────────────

def get_last_scrape() -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM scrape_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_scrape_history(limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM scrape_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Dashboard stats ───────────────────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    conn = get_connection()
    stats = {}
    stats["total_jobs"] = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    stats["new_this_week"] = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE posted_date >= date('now','-7 days')"
    ).fetchone()[0]
    stats["total_applications"] = conn.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]
    stats["active_applications"] = conn.execute(
        "SELECT COUNT(*) FROM applications "
        "WHERE status NOT IN ('Rejected','Withdrawn','Offer')"
    ).fetchone()[0]
    stats["by_category"] = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT category, COUNT(*) FROM jobs GROUP BY category ORDER BY 2 DESC"
        ).fetchall()
        if r[0]
    }
    stats["by_status"] = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT status, COUNT(*) FROM applications GROUP BY status"
        ).fetchall()
        if r[0]
    }
    stats["top_sources"] = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT source, COUNT(*) FROM jobs GROUP BY source ORDER BY 2 DESC LIMIT 5"
        ).fetchall()
        if r[0]
    }
    stats["avg_match"] = conn.execute(
        "SELECT ROUND(AVG(match_score),1) FROM jobs WHERE match_score > 0"
    ).fetchone()[0] or 0
    conn.close()
    return stats


# ── Seed ──────────────────────────────────────────────────────────────────────

def _seed_sample_jobs(cur: sqlite3.Cursor) -> None:
    from jobs import SAMPLE_JOBS
    inserted = 0
    for job in SAMPLE_JOBS:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO jobs
                  (title,organization,location,state,category,source,
                   salary_min,salary_max,description,requirements,url,
                   posted_date,closing_date,employment_type,is_pr_relevant)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                job["title"], job["organization"], job["location"],
                job.get("state", "ACT"), job["category"], job["source"],
                job["salary_min"], job["salary_max"],
                job["description"], job["requirements"],
                job["url"], job["posted_date"], job["closing_date"],
                job.get("employment_type", "Full-time"), 1,
            ))
            if cur.lastrowid:
                inserted += 1
        except Exception as exc:
            logger.warning("Seed job '%s' failed: %s", job.get("title"), exc)
    logger.info("Seeded %d sample jobs", inserted)


def _seed_default_profile(cur: sqlite3.Cursor) -> None:
    """Pre-fill user_profile with Mohammad Almomani's details on first run."""
    existing = cur.execute("SELECT id FROM user_profile LIMIT 1").fetchone()
    if existing:
        return
    try:
        from config import DEFAULT_PROFILE
        cur.execute("""
            INSERT INTO user_profile
              (name, email, phone, linkedin, visa_status,
               skills, experience, education, target_roles)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            DEFAULT_PROFILE["name"],
            DEFAULT_PROFILE["email"],
            DEFAULT_PROFILE["phone"],
            DEFAULT_PROFILE.get("linkedin", ""),
            DEFAULT_PROFILE.get("visa_status", "Skilled Independent (189)"),
            DEFAULT_PROFILE.get("data_skills", ""),
            (
                f"{DEFAULT_PROFILE.get('years_experience', 7)} years combined "
                "academic and industry experience. "
                f"{DEFAULT_PROFILE.get('econometric_methods', '')}"
            ),
            DEFAULT_PROFILE.get("qualification", ""),
            (
                "Health Economist, Research Fellow, Economist, Policy Analyst, "
                "Lecturer, Government Research Officer, Evaluation Specialist, "
                "Data Analyst, Business Intelligence Analyst"
            ),
        ))
        logger.info("Seeded default profile for %s", DEFAULT_PROFILE["name"])
    except Exception as exc:
        logger.warning("Profile seed failed: %s", exc)
