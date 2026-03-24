"""
utils/data_store.py
====================
Persistent SQLite storage for OS/DB lifecycle data and Agent 2 recommendations.

On Agent 2 completion  → saves full OS + DB dataframes to SQLite
On app load            → loads from SQLite (not baseline) so admin sees saved state
On Agent 1 change      → updates only rows that changed, preserves recommendations
On baseline first load → saves baseline to SQLite so it's immediately persistent
"""
import sqlite3
import pandas as pd
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "lifecycle_data.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")   # concurrent read-safe
    conn.execute("""
        CREATE TABLE IF NOT EXISTS os_versions (
            os_version          TEXT PRIMARY KEY,
            availability_date   TEXT,
            security_end        TEXT,
            mainstream_end      TEXT,
            extended_end        TEXT,
            notes               TEXT,
            recommendation      TEXT DEFAULT '',
            upgrade             TEXT DEFAULT 'N',
            replace_flag        TEXT DEFAULT 'N',
            primary_alt         TEXT DEFAULT '',
            secondary_alt       TEXT DEFAULT '',
            policy_rec          TEXT DEFAULT '',
            final_rec           TEXT DEFAULT '',
            final_verdict       TEXT DEFAULT '',
            analysis_source     TEXT DEFAULT '',
            updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS db_versions (
            db_key              TEXT PRIMARY KEY,
            database_name       TEXT,
            version             TEXT,
            db_type             TEXT,
            mainstream_end      TEXT,
            extended_end        TEXT,
            status              TEXT,
            notes               TEXT,
            recommendation      TEXT DEFAULT '',
            upgrade             TEXT DEFAULT 'N',
            replace_flag        TEXT DEFAULT 'N',
            primary_alt         TEXT DEFAULT '',
            secondary_alt       TEXT DEFAULT '',
            policy_rec          TEXT DEFAULT '',
            final_rec           TEXT DEFAULT '',
            final_verdict       TEXT DEFAULT '',
            analysis_source     TEXT DEFAULT '',
            updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            key     TEXT PRIMARY KEY,
            value   TEXT,
            updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit()
    return conn


# ── OS helpers ─────────────────────────────────────────────────────────────────

def save_os_df(df: pd.DataFrame):
    """Upsert full OS dataframe to SQLite. Preserves existing recommendations if new value is blank."""
    conn = _get_conn()
    ts = datetime.now().isoformat()
    for _, row in df.iterrows():
        key = str(row.get("OS Version", "")).strip()
        if not key:
            continue
        # Load existing rec so we don't overwrite with blank
        existing = conn.execute(
            "SELECT recommendation, policy_rec, final_rec FROM os_versions WHERE os_version=?", (key,)
        ).fetchone()
        rec     = str(row.get("Recommendation", "")).strip()     or (existing[0] if existing else "")
        pol_rec = str(row.get("Policy Recommendation", "")).strip() or (existing[1] if existing else "")
        fin_rec = str(row.get("Final Recommendation", "")).strip()  or (existing[2] if existing else "")

        conn.execute("""
            INSERT INTO os_versions
                (os_version, availability_date, security_end, mainstream_end, extended_end,
                 notes, recommendation, upgrade, replace_flag, primary_alt, secondary_alt,
                 policy_rec, final_rec, final_verdict, analysis_source, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(os_version) DO UPDATE SET
                availability_date=excluded.availability_date,
                security_end=excluded.security_end,
                mainstream_end=excluded.mainstream_end,
                extended_end=excluded.extended_end,
                notes=excluded.notes,
                recommendation=CASE WHEN excluded.recommendation != '' THEN excluded.recommendation ELSE recommendation END,
                upgrade=excluded.upgrade,
                replace_flag=excluded.replace_flag,
                primary_alt=excluded.primary_alt,
                secondary_alt=excluded.secondary_alt,
                policy_rec=CASE WHEN excluded.policy_rec != '' THEN excluded.policy_rec ELSE policy_rec END,
                final_rec=CASE WHEN excluded.final_rec != '' THEN excluded.final_rec ELSE final_rec END,
                final_verdict=excluded.final_verdict,
                analysis_source=excluded.analysis_source,
                updated_at=excluded.updated_at
        """, (
            key,
            str(row.get("Availability Date", "")),
            str(row.get("Security/Standard Support End", "")),
            str(row.get("Mainstream/Full Support End", "")),
            str(row.get("Extended/LTSC Support End", "")),
            str(row.get("Notes", "")),
            rec, pol_rec, fin_rec,
            str(row.get("Upgrade", "N")),
            str(row.get("Replace", "N")),
            str(row.get("Primary Alternative", "")),
            str(row.get("Secondary Alternative", "")),
            pol_rec, fin_rec,
            str(row.get("Final Verdict", "")),
            str(row.get("Analysis Source", "")),
            ts
        ))
    conn.commit()
    conn.close()


def load_os_df() -> pd.DataFrame:
    """Load OS dataframe from SQLite. Returns empty df if nothing stored yet."""
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT os_version, availability_date, security_end, mainstream_end, extended_end,
                   notes, recommendation, upgrade, replace_flag, primary_alt, secondary_alt,
                   policy_rec, final_rec, final_verdict, analysis_source
            FROM os_versions ORDER BY os_version
        """).fetchall()
        conn.close()
        if not rows:
            return pd.DataFrame()
        cols = ["OS Version","Availability Date","Security/Standard Support End",
                "Mainstream/Full Support End","Extended/LTSC Support End","Notes",
                "Recommendation","Upgrade","Replace","Primary Alternative","Secondary Alternative",
                "Policy Recommendation","Final Recommendation","Final Verdict","Analysis Source"]
        return pd.DataFrame(rows, columns=cols)
    except Exception:
        return pd.DataFrame()


# ── DB helpers ─────────────────────────────────────────────────────────────────

def save_db_df(df: pd.DataFrame):
    """Upsert full DB dataframe to SQLite."""
    conn = _get_conn()
    ts = datetime.now().isoformat()
    for _, row in df.iterrows():
        db_name = str(row.get("Database", "")).strip()
        version = str(row.get("Version", "")).strip()
        key     = f"{db_name}||{version}"
        if not db_name:
            continue
        existing = conn.execute(
            "SELECT recommendation, policy_rec, final_rec FROM db_versions WHERE db_key=?", (key,)
        ).fetchone()
        rec     = str(row.get("Recommendation", "")).strip()       or (existing[0] if existing else "")
        pol_rec = str(row.get("Policy Recommendation", "")).strip() or (existing[1] if existing else "")
        fin_rec = str(row.get("Final Recommendation", "")).strip()  or (existing[2] if existing else "")

        conn.execute("""
            INSERT INTO db_versions
                (db_key, database_name, version, db_type, mainstream_end, extended_end,
                 status, notes, recommendation, upgrade, replace_flag, primary_alt, secondary_alt,
                 policy_rec, final_rec, final_verdict, analysis_source, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(db_key) DO UPDATE SET
                db_type=excluded.db_type,
                mainstream_end=excluded.mainstream_end,
                extended_end=excluded.extended_end,
                status=excluded.status,
                notes=excluded.notes,
                recommendation=CASE WHEN excluded.recommendation != '' THEN excluded.recommendation ELSE recommendation END,
                upgrade=excluded.upgrade,
                replace_flag=excluded.replace_flag,
                primary_alt=excluded.primary_alt,
                secondary_alt=excluded.secondary_alt,
                policy_rec=CASE WHEN excluded.policy_rec != '' THEN excluded.policy_rec ELSE policy_rec END,
                final_rec=CASE WHEN excluded.final_rec != '' THEN excluded.final_rec ELSE final_rec END,
                final_verdict=excluded.final_verdict,
                analysis_source=excluded.analysis_source,
                updated_at=excluded.updated_at
        """, (
            key, db_name, version,
            str(row.get("Type", "")),
            str(row.get("Mainstream / Premier End", "")),
            str(row.get("Extended Support End", "")),
            str(row.get("Status", "Supported")),
            str(row.get("Notes", "")),
            rec,
            str(row.get("Upgrade", "N")),
            str(row.get("Replace", "N")),
            str(row.get("Primary Alternative", "")),
            str(row.get("Secondary Alternative", "")),
            pol_rec, fin_rec,
            str(row.get("Final Verdict", "")),
            str(row.get("Analysis Source", "")),
            ts
        ))
    conn.commit()
    conn.close()


def load_db_df() -> pd.DataFrame:
    """Load DB dataframe from SQLite."""
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT database_name, version, db_type, mainstream_end, extended_end,
                   status, notes, recommendation, upgrade, replace_flag, primary_alt, secondary_alt,
                   policy_rec, final_rec, final_verdict, analysis_source
            FROM db_versions ORDER BY database_name, version
        """).fetchall()
        conn.close()
        if not rows:
            return pd.DataFrame()
        cols = ["Database","Version","Type","Mainstream / Premier End","Extended Support End",
                "Status","Notes","Recommendation","Upgrade","Replace",
                "Primary Alternative","Secondary Alternative",
                "Policy Recommendation","Final Recommendation","Final Verdict","Analysis Source"]
        return pd.DataFrame(rows, columns=cols)
    except Exception:
        return pd.DataFrame()


# ── App state helpers ──────────────────────────────────────────────────────────

def save_app_state(key: str, value):
    conn = _get_conn()
    conn.execute("""
        INSERT INTO app_state (key, value, updated) VALUES (?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=CURRENT_TIMESTAMP
    """, (key, json.dumps(value)))
    conn.commit()
    conn.close()


def load_app_state(key: str, default=None):
    try:
        conn = _get_conn()
        row = conn.execute("SELECT value FROM app_state WHERE key=?", (key,)).fetchone()
        conn.close()
        return json.loads(row[0]) if row else default
    except Exception:
        return default


def get_rec_stats() -> dict:
    """Return counts of how many rows have recommendations stored."""
    try:
        conn = _get_conn()
        os_total   = conn.execute("SELECT COUNT(*) FROM os_versions").fetchone()[0]
        os_with    = conn.execute("SELECT COUNT(*) FROM os_versions WHERE recommendation != ''").fetchone()[0]
        db_total   = conn.execute("SELECT COUNT(*) FROM db_versions").fetchone()[0]
        db_with    = conn.execute("SELECT COUNT(*) FROM db_versions WHERE recommendation != ''").fetchone()[0]
        last_saved = conn.execute(
            "SELECT MAX(updated_at) FROM os_versions WHERE recommendation != ''"
        ).fetchone()[0]
        conn.close()
        return {
            "os_total": os_total, "os_with_recs": os_with,
            "db_total": db_total, "db_with_recs": db_with,
            "last_saved": last_saved or "Never"
        }
    except Exception:
        return {"os_total": 0, "os_with_recs": 0, "db_total": 0,
                "db_with_recs": 0, "last_saved": "Never"}


def has_stored_data() -> bool:
    """True if SQLite has any OS/DB rows — i.e. not first run."""
    try:
        conn = _get_conn()
        n = conn.execute("SELECT COUNT(*) FROM os_versions").fetchone()[0]
        conn.close()
        return n > 0
    except Exception:
        return False
