"""
Agent 5: Conversational Policy Analysis Agent
Uses ONLY gpt-4o-mini via chat.completions — no Responses API, no search models.
"""
from openai import OpenAI
import json
import sqlite3
import os
import pandas as pd
import streamlit as st
from datetime import date, datetime

PROJECT_END = date(2028, 6, 30)
TODAY       = date.today()
DB_PATH     = "/tmp/agent5_conversations.db"   # /tmp is writable on Streamlit Cloud

VERDICTS = ["CRITICAL", "UPGRADE NOW", "EXTEND + PLAN", "REPLACE", "CLOUD MIGRATE", "MONITOR"]

CONVERSATION_SYSTEM = f"""You are Agent 5 — a senior IT migration strategist at Infosys.
Help an enterprise architect define their OS and database migration policy
for a project running from 1 April 2026 to 30 June 2028.

Have a NATURAL CONVERSATION. Ask ONE focused question at a time.
For cost/pricing questions, use your training knowledge and give best estimates with caveats.

Cover these topics across the conversation:
1. EOL risk tolerance
2. Support runway needed at project end (Jun 2028)
3. Budget — ESU approved? Cloud budget?
4. Compliance — PCI DSS / HIPAA / SOX / GDPR
5. Windows EOL path
6. Linux/Unix/AIX path
7. Database EOL path
8. Oracle licensing stance
9. Cloud provider preference
10. Legacy DB stance (Informix, SAP ASE, Progress, Ingres)
11. Migration capacity
12. System criticality tiers
13. Rollback policy

After 10-15 exchanges with sufficient context, respond with ONLY this JSON:
{{"ready": true, "summary": "2-3 sentence summary", "context": {{"key": "value"}}}}
Today: {TODAY}. Project ends 30 Jun 2028."""

PRINCIPLES_SYSTEM = """Generate 8-10 Guiding Principles (GP-01...GP-10) from a policy conversation.
Return ONLY a JSON array:
[{{"code":"GP-01","title":"Short title","rule":"One rule.","trigger":"If X then Y","category":"Risk|Budget|OS|Database|Execution"}}]"""

FINAL_REC_SYSTEM = f"""Cross-reference Agent 2 technical recommendations with org policy to produce
Final Recommendations. Project: 1 Apr 2026 to 30 Jun 2028. Today: {TODAY}.
Start each with: CRITICAL / UPGRADE NOW / EXTEND + PLAN / REPLACE / CLOUD MIGRATE / MONITOR
Return ONLY JSON: {{"KEY": "VERDICT — recommendation. (GP-N)"}}"""


# ── SQLite helpers ─────────────────────────────────────────────────────────────
def _get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session TEXT NOT NULL, role TEXT NOT NULL,
        content TEXT NOT NULL, ts DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
        session TEXT PRIMARY KEY, context TEXT, summary TEXT,
        status TEXT DEFAULT 'chatting',
        created DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    return conn

def _save_message(session_id, role, content):
    conn = _get_db()
    conn.execute("INSERT INTO conversations (session,role,content) VALUES (?,?,?)",
                 (session_id, role, content))
    conn.execute("INSERT OR IGNORE INTO sessions (session) VALUES (?)", (session_id,))
    conn.execute("UPDATE sessions SET updated=CURRENT_TIMESTAMP WHERE session=?", (session_id,))
    conn.commit(); conn.close()

def _load_messages(session_id):
    conn = _get_db()
    rows = conn.execute(
        "SELECT role,content FROM conversations WHERE session=? ORDER BY id",
        (session_id,)).fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in rows]

def _save_session_context(session_id, context, summary, status):
    conn = _get_db()
    conn.execute("""INSERT INTO sessions (session,context,summary,status)
        VALUES (?,?,?,?) ON CONFLICT(session) DO UPDATE SET
        context=excluded.context, summary=excluded.summary,
        status=excluded.status, updated=CURRENT_TIMESTAMP""",
        (session_id, json.dumps(context), summary, status))
    conn.commit(); conn.close()

def _list_sessions():
    conn = _get_db()
    rows = conn.execute(
        "SELECT session,summary,status,updated FROM sessions ORDER BY updated DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return [{"session": r[0], "summary": r[1] or "In progress",
             "status": r[2], "updated": r[3]} for r in rows]

def _delete_session(session_id):
    conn = _get_db()
    conn.execute("DELETE FROM conversations WHERE session=?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE session=?", (session_id,))
    conn.commit(); conn.close()



MODEL_PREFERENCE = ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-3.5-turbo-0125"]

def _resolve_model(client):
    """Try models in order, return first that works. Cache in session_state."""
    import streamlit as st
    cached = st.session_state.get("_openai_model")
    if cached:
        return cached
    for model in MODEL_PREFERENCE:
        try:
            client.chat.completions.create(
                model=model, max_tokens=5,
                messages=[{"role": "user", "content": "ping"}]
            )
            st.session_state["_openai_model"] = model
            return model
        except Exception as e:
            err = str(e).lower()
            if "not found" in err or "404" in err or "model" in err:
                continue
            st.session_state["_openai_model"] = model
            return model
    return MODEL_PREFERENCE[0]

class PolicyAnalysisAgent:

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model  = _resolve_model(self.client)

    @staticmethod
    def get_or_create_session():
        if "a5_session_id" not in st.session_state:
            import uuid
            st.session_state.a5_session_id = str(uuid.uuid4())[:8]
        return st.session_state.a5_session_id

    @staticmethod
    def init_session():
        defaults = {
            "a5_status": "idle", "a5_context": {}, "a5_principles": [],
            "a5_costs": {}, "a5_os_done": False, "a5_db_done": False,
            "a5_preflight_done": False, "a5_log": [],
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    @staticmethod
    def reset():
        session_id = st.session_state.get("a5_session_id")
        if session_id:
            _delete_session(session_id)
        for k in ["a5_status","a5_session_id","a5_context","a5_principles",
                  "a5_costs","a5_os_done","a5_db_done","a5_preflight_done","a5_log"]:
            st.session_state.pop(k, None)
        PolicyAnalysisAgent.init_session()

    def chat(self, messages: list) -> str:
        """Send conversation to gpt-4o-mini via chat.completions."""
        api_messages = [{"role": "system", "content": CONVERSATION_SYSTEM}]
        if messages:
            api_messages += messages[-20:]
        else:
            api_messages.append({"role": "user",
                                  "content": "Start the policy conversation now."})

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=700,
            messages=api_messages
        )
        return response.choices[0].message.content.strip()

    def is_conversation_complete(self, reply: str) -> tuple:
        try:
            s, e = reply.find("{"), reply.rfind("}")
            if s != -1 and e > s:
                data = json.loads(reply[s:e+1])
                if data.get("ready"):
                    return True, data.get("context", {}), data.get("summary", "")
        except Exception:
            pass
        return False, {}, ""

    def generate_principles(self, context: dict, session_id: str) -> list:
        messages = _load_messages(session_id)
        conv = "\n".join(
            f"{'ARCHITECT' if m['role']=='user' else 'AGENT5'}: {m['content'][:200]}"
            for m in messages[-24:])
        ctx  = "\n".join(f"{k}: {v}" for k, v in context.items())
        try:
            resp = self.client.chat.completions.create(
                model=self.model, max_tokens=2500,
                messages=[
                    {"role": "system", "content": PRINCIPLES_SYSTEM},
                    {"role": "user",   "content": f"CONTEXT:\n{ctx}\n\nCONVERSATION:\n{conv}"}
                ])
            text = resp.choices[0].message.content.strip()
            if "```" in text:
                text = text.split("```json")[-1].split("```")[0] if "```json" in text \
                       else text.split("```")[1].split("```")[0]
            s, e = text.find("["), text.rfind("]")
            if s != -1 and e > s:
                return json.loads(text[s:e+1])
        except Exception:
            pass
        return [{"code": "GP-01", "title": "Zero EOL Tolerance",
                 "rule": "No EOL software past 30 Jun 2028.",
                 "trigger": "EOL before Jun 2028 → Upgrade", "category": "Risk"}]

    def fetch_costs(self, progress_cb=None) -> dict:
        queries = [
            ("Windows Server ESU",
             "Windows Server 2016 and 2019 Extended Security Updates estimated cost per server per year. Include Azure Arc free ESU option."),
            ("SQL Server ESU",
             "SQL Server 2016 2017 2019 Extended Security Updates estimated cost per core per year."),
            ("Oracle Database Support",
             "Oracle Database annual support cost approximately 22 percent of license. Extended support surcharge details."),
            ("RHEL Subscription",
             "Red Hat Enterprise Linux RHEL Standard and Premium subscription cost per server per year estimates."),
            ("Cloud DB Pricing",
             "Azure SQL Managed Instance and AWS RDS Aurora PostgreSQL approximate monthly cost per instance."),
            ("Migration Tools",
             "AWS Database Migration Service and Azure Database Migration Service approximate cost per hour."),
        ]
        costs = {}
        fallbacks = {
            "Windows Server ESU":
                "Windows Server 2016 ESU: ~$198/server/yr (Yr1), ~$396 (Yr2). Free via Azure Arc. Server 2019: ESU from 2029.",
            "SQL Server ESU":
                "SQL Server 2016 ESU: ~$1,418/core/yr. SQL Server 2019 mainstream support ends Jan 2025; extended until Jan 2030 (no ESU needed yet).",
            "Oracle Database Support":
                "Oracle annual support: ~22% of license list price. Extended Support (years 4-5) adds 10% surcharge (~32% total).",
            "RHEL Subscription":
                "RHEL Standard: ~$800/yr/socket-pair. RHEL Premium (24x7 support): ~$1,300/yr/socket-pair.",
            "Cloud DB Pricing":
                "Azure SQL MI (4 vCores, GP): ~$465/mo. AWS RDS PostgreSQL db.t3.medium: ~$60/mo. Aurora PostgreSQL: ~$200/mo.",
            "Migration Tools":
                "AWS DMS: ~$0.18/hr per replication instance + data transfer. Azure DMS Standard: ~$0.10/hr.",
        }
        for i, (vendor, query) in enumerate(queries):
            if progress_cb:
                progress_cb(i / len(queries), f"Fetching cost estimate: {vendor}...")
            try:
                resp = self.client.chat.completions.create(
                    model=self.model, max_tokens=300,
                    messages=[{"role": "user", "content":
                        f"Based on your training knowledge, give a 2-3 sentence cost estimate for: {query}\n"
                        f"Note that figures are approximate and may have changed since your training cutoff."}])
                result = resp.choices[0].message.content.strip()
                costs[vendor] = result or fallbacks[vendor]
            except Exception:
                costs[vendor] = fallbacks[vendor]
        if progress_cb:
            progress_cb(1.0, "✅ Cost estimates ready.")
        return costs

    def analyse_os(self, df, principles, costs, context, progress_cb=None):
        return self._analyse(df, "OS", principles, costs, context, progress_cb)

    def analyse_db(self, df, principles, costs, context, progress_cb=None):
        return self._analyse(df, "DB", principles, costs, context, progress_cb)

    def _analyse(self, df, kind, principles, costs, context, progress_cb):
        df = df.copy()
        for col in ["Final Recommendation", "Final Verdict", "Analysis Source"]:
            if col not in df.columns:
                df[col] = ""

        gp_text   = "\n".join(f"{p['code']}: {p['title']} — {p['rule']}" for p in principles)
        cost_text = "\n".join(f"{v}: {s}" for v, s in costs.items())
        ctx_text  = "\n".join(f"{k}: {v}" for k, v in context.items())
        rows = df.to_dict("records")
        total = len(rows); batch = 15
        ai_count = 0; rb_count = 0

        for i in range(0, total, batch):
            chunk = rows[i:i+batch]
            if progress_cb:
                progress_cb(i / total,
                    f"🧠 Generating Final Recommendations — {kind} rows {i+1}–{min(i+batch,total)} of {total}...")

            rows_text = "\n".join(
                f"KEY={r['OS Version']} | Mainstream={r.get('Mainstream/Full Support End','')} | "
                f"Extended={r.get('Extended/LTSC Support End','')} | "
                f"Agent2={r.get('Recommendation','')[:120]}"
                for r in chunk
            ) if kind == "OS" else "\n".join(
                f"KEY={r['Database']} {r['Version']} | Status={r.get('Status','')} | "
                f"Extended={r.get('Extended Support End','')} | "
                f"Replace={r.get('Replace','')} | Alt={r.get('Primary Alternative','')} | "
                f"Agent2={r.get('Recommendation','')[:120]}"
                for r in chunk
            )

            prompt = (f"ORG POLICY:\n{ctx_text}\n\nGUIDING PRINCIPLES:\n{gp_text}\n\n"
                      f"VENDOR COSTS:\n{cost_text}\n\n"
                      f"PROJECT: 1 Apr 2026 → 30 Jun 2028 | Today: {TODAY}\n\n"
                      f"RECORDS:\n{rows_text}\n\n"
                      f"Return ONLY JSON: {{\"KEY\": \"VERDICT — recommendation. (GP-N)\"}}")

            recs = {}; api_worked = False
            for attempt in range(2):
                try:
                    import time
                    if attempt > 0: time.sleep(2)
                    resp = self.client.chat.completions.create(
                        model=self.model, max_tokens=4000,
                        messages=[
                            {"role": "system", "content": FINAL_REC_SYSTEM},
                            {"role": "user",   "content": prompt}
                        ])
                    text = resp.choices[0].message.content.strip()
                    if "```" in text:
                        text = text.split("```json")[-1].split("```")[0] if "```json" in text \
                               else text.split("```")[1].split("```")[0]
                    s, e = text.find("{"), text.rfind("}")
                    parsed = json.loads(text[s:e+1]) if s != -1 and e > s else {}
                    if parsed:
                        recs = parsed; api_worked = True; break
                except Exception as ex:
                    last_error = str(ex)

            for j, row in enumerate(chunk):
                key = row["OS Version"] if kind == "OS" \
                      else f"{row['Database']} {row['Version']}"
                if key in recs:
                    rec = recs[key]; source = "OpenAI"; ai_count += 1
                else:
                    rec = self._rule_based(row, kind); source = "Rule-based"; rb_count += 1
                verdict = next((v for v in VERDICTS if rec.upper().startswith(v)), "MONITOR")
                df.at[i+j, "Final Recommendation"] = rec
                df.at[i+j, "Final Verdict"]        = verdict
                df.at[i+j, "Analysis Source"]      = source

            import time as _t; _t.sleep(0.3)

        if progress_cb:
            progress_cb(1.0, f"✅ {kind} done — OpenAI: {ai_count} | Rule-based: {rb_count}")
        return df

    def _rule_based(self, row, kind):
        def _parse(s):
            try: return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
            except: return None
        if kind == "OS":
            end  = _parse(row.get("Extended/LTSC Support End","")) \
                or _parse(row.get("Mainstream/Full Support End",""))
            name = row.get("OS Version", "?")
        else:
            end  = _parse(row.get("Extended Support End","")) \
                or _parse(row.get("Mainstream / Premier End",""))
            name = f"{row.get('Database','?')} {row.get('Version','?')}"
        if not end:
            return f"MONITOR — Verify support dates for {name}. (GP-02)"
        if end < TODAY:
            return f"CRITICAL — {name} EOL as of {end}. Immediate action required. (GP-01)"
        if end < PROJECT_END:
            return f"UPGRADE NOW — {name} ends {end}, before Jun 2028. Act now. (GP-01)"
        if end < date(2030, 6, 30):
            return f"EXTEND + PLAN — {name} until {end}. Plan upgrade within project. (GP-02)"
        return f"MONITOR — {name} until {end}, past project end. No immediate action. (GP-05)"
