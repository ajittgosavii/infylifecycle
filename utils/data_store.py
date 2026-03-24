"""
utils/data_store.py — SQLite persistence for OS/DB data and recommendations.
Saves on Agent 1/2/5 completion. Loads on every app start — no data lost on refresh.
"""
import sqlite3, json, os, pandas as pd
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "lifecycle_data.db")


def _conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS os_versions (
        os_version    TEXT PRIMARY KEY,
        avail_date    TEXT DEFAULT '',
        sec_end       TEXT DEFAULT '',
        main_end      TEXT DEFAULT '',
        ext_end       TEXT DEFAULT '',
        notes         TEXT DEFAULT '',
        recommendation TEXT DEFAULT '',
        upgrade       TEXT DEFAULT 'N',
        replace_flag  TEXT DEFAULT 'N',
        primary_alt   TEXT DEFAULT '',
        secondary_alt TEXT DEFAULT '',
        final_rec     TEXT DEFAULT '',
        final_verdict TEXT DEFAULT '',
        analysis_src  TEXT DEFAULT '',
        updated_at    TEXT DEFAULT ''
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS db_versions (
        db_key        TEXT PRIMARY KEY,
        db_name       TEXT DEFAULT '',
        version       TEXT DEFAULT '',
        db_type       TEXT DEFAULT '',
        main_end      TEXT DEFAULT '',
        ext_end       TEXT DEFAULT '',
        status        TEXT DEFAULT '',
        notes         TEXT DEFAULT '',
        recommendation TEXT DEFAULT '',
        upgrade       TEXT DEFAULT 'N',
        replace_flag  TEXT DEFAULT 'N',
        primary_alt   TEXT DEFAULT '',
        secondary_alt TEXT DEFAULT '',
        final_rec     TEXT DEFAULT '',
        final_verdict TEXT DEFAULT '',
        analysis_src  TEXT DEFAULT '',
        updated_at    TEXT DEFAULT ''
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS app_state (
        key TEXT PRIMARY KEY, value TEXT DEFAULT '', updated TEXT DEFAULT ''
    )""")
    c.commit()
    return c


# ── OS ─────────────────────────────────────────────────────────────────────────

def save_os_df(df: pd.DataFrame):
    c = _conn(); ts = datetime.now().isoformat()
    for _, r in df.iterrows():
        key = str(r.get("OS Version", "")).strip()
        if not key:
            continue
        ex  = c.execute("SELECT recommendation,final_rec FROM os_versions WHERE os_version=?",
                        (key,)).fetchone()
        rec = str(r.get("Recommendation","")).strip()       or (ex[0] if ex else "")
        fin = str(r.get("Final Recommendation","")).strip() or (ex[1] if ex else "")
        # 15 columns → 15 placeholders → 15 values
        c.execute("""
            INSERT INTO os_versions
              (os_version,avail_date,sec_end,main_end,ext_end,notes,
               recommendation,upgrade,replace_flag,primary_alt,secondary_alt,
               final_rec,final_verdict,analysis_src,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(os_version) DO UPDATE SET
              avail_date=excluded.avail_date, sec_end=excluded.sec_end,
              main_end=excluded.main_end, ext_end=excluded.ext_end,
              notes=excluded.notes,
              recommendation=CASE WHEN excluded.recommendation!='' THEN excluded.recommendation ELSE recommendation END,
              upgrade=excluded.upgrade, replace_flag=excluded.replace_flag,
              primary_alt=excluded.primary_alt, secondary_alt=excluded.secondary_alt,
              final_rec=CASE WHEN excluded.final_rec!='' THEN excluded.final_rec ELSE final_rec END,
              final_verdict=excluded.final_verdict, analysis_src=excluded.analysis_src,
              updated_at=excluded.updated_at
        """, (key,
              str(r.get("Availability Date","")),
              str(r.get("Security/Standard Support End","")),
              str(r.get("Mainstream/Full Support End","")),
              str(r.get("Extended/LTSC Support End","")),
              str(r.get("Notes","")),
              rec,
              str(r.get("Upgrade","N")),
              str(r.get("Replace","N")),
              str(r.get("Primary Alternative","")),
              str(r.get("Secondary Alternative","")),
              fin,
              str(r.get("Final Verdict","")),
              str(r.get("Analysis Source","")),
              ts))
    c.commit(); c.close()


def load_os_df() -> pd.DataFrame:
    try:
        c = _conn()
        rows = c.execute("""SELECT os_version,avail_date,sec_end,main_end,ext_end,notes,
               recommendation,upgrade,replace_flag,primary_alt,secondary_alt,
               final_rec,final_verdict,analysis_src FROM os_versions ORDER BY os_version
        """).fetchall()
        c.close()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=[
            "OS Version","Availability Date","Security/Standard Support End",
            "Mainstream/Full Support End","Extended/LTSC Support End","Notes",
            "Recommendation","Upgrade","Replace","Primary Alternative","Secondary Alternative",
            "Final Recommendation","Final Verdict","Analysis Source"])
    except Exception:
        return pd.DataFrame()


# ── DB ─────────────────────────────────────────────────────────────────────────

def save_db_df(df: pd.DataFrame):
    c = _conn(); ts = datetime.now().isoformat()
    for _, r in df.iterrows():
        db_name = str(r.get("Database","")).strip()
        version = str(r.get("Version","")).strip()
        key     = f"{db_name}||{version}"
        if not db_name:
            continue
        ex  = c.execute("SELECT recommendation,final_rec FROM db_versions WHERE db_key=?",
                        (key,)).fetchone()
        rec = str(r.get("Recommendation","")).strip()       or (ex[0] if ex else "")
        fin = str(r.get("Final Recommendation","")).strip() or (ex[1] if ex else "")
        # 17 columns → 17 placeholders → 17 values
        c.execute("""
            INSERT INTO db_versions
              (db_key,db_name,version,db_type,main_end,ext_end,status,notes,
               recommendation,upgrade,replace_flag,primary_alt,secondary_alt,
               final_rec,final_verdict,analysis_src,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(db_key) DO UPDATE SET
              db_type=excluded.db_type, main_end=excluded.main_end,
              ext_end=excluded.ext_end, status=excluded.status, notes=excluded.notes,
              recommendation=CASE WHEN excluded.recommendation!='' THEN excluded.recommendation ELSE recommendation END,
              upgrade=excluded.upgrade, replace_flag=excluded.replace_flag,
              primary_alt=excluded.primary_alt, secondary_alt=excluded.secondary_alt,
              final_rec=CASE WHEN excluded.final_rec!='' THEN excluded.final_rec ELSE final_rec END,
              final_verdict=excluded.final_verdict, analysis_src=excluded.analysis_src,
              updated_at=excluded.updated_at
        """, (key, db_name, version,
              str(r.get("Type","")),
              str(r.get("Mainstream / Premier End","")),
              str(r.get("Extended Support End","")),
              str(r.get("Status","Supported")),
              str(r.get("Notes","")),
              rec,
              str(r.get("Upgrade","N")),
              str(r.get("Replace","N")),
              str(r.get("Primary Alternative","")),
              str(r.get("Secondary Alternative","")),
              fin,
              str(r.get("Final Verdict","")),
              str(r.get("Analysis Source","")),
              ts))
    c.commit(); c.close()


def load_db_df() -> pd.DataFrame:
    try:
        c = _conn()
        rows = c.execute("""SELECT db_name,version,db_type,main_end,ext_end,status,notes,
               recommendation,upgrade,replace_flag,primary_alt,secondary_alt,
               final_rec,final_verdict,analysis_src FROM db_versions ORDER BY db_name,version
        """).fetchall()
        c.close()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=[
            "Database","Version","Type","Mainstream / Premier End","Extended Support End",
            "Status","Notes","Recommendation","Upgrade","Replace",
            "Primary Alternative","Secondary Alternative",
            "Final Recommendation","Final Verdict","Analysis Source"])
    except Exception:
        return pd.DataFrame()


# ── App state ──────────────────────────────────────────────────────────────────

def save_app_state(key: str, value):
    c = _conn()
    c.execute("""INSERT INTO app_state(key,value,updated) VALUES(?,?,?)
                 ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated=excluded.updated""",
              (key, json.dumps(value), datetime.now().isoformat()))
    c.commit(); c.close()


def load_app_state(key: str, default=None):
    try:
        c = _conn()
        row = c.execute("SELECT value FROM app_state WHERE key=?", (key,)).fetchone()
        c.close()
        return json.loads(row[0]) if row else default
    except Exception:
        return default


def has_stored_data() -> bool:
    try:
        c = _conn()
        n = c.execute("SELECT COUNT(*) FROM os_versions").fetchone()[0]
        c.close()
        return n > 0
    except Exception:
        return False


def get_rec_stats() -> dict:
    try:
        c = _conn()
        ot = c.execute("SELECT COUNT(*) FROM os_versions").fetchone()[0]
        ow = c.execute("SELECT COUNT(*) FROM os_versions WHERE recommendation!=''").fetchone()[0]
        dt = c.execute("SELECT COUNT(*) FROM db_versions").fetchone()[0]
        dw = c.execute("SELECT COUNT(*) FROM db_versions WHERE recommendation!=''").fetchone()[0]
        ls = c.execute("SELECT MAX(updated_at) FROM os_versions WHERE recommendation!=''").fetchone()[0]
        c.close()
        return {"os_total":ot,"os_with_recs":ow,"db_total":dt,"db_with_recs":dw,
                "last_saved": ls or "Never"}
    except Exception:
        return {"os_total":0,"os_with_recs":0,"db_total":0,"db_with_recs":0,"last_saved":"Never"}
