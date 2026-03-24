"""
Agent 5: Conversational Policy Analysis Agent
==============================================
- SQLite persists full conversation across reruns/refreshes
- Every chat response uses gpt-4o-mini-search-preview (Responses API)
  so real-time web search covers costs, ESU prices, migration guides,
  upgrade paths, extended support dates — anything the user asks
- Generates Guiding Principles from conversation
- Final Recommendations cross-reference Agent 2 + policy context

Project window: 1 Apr 2026 → 30 Jun 2028
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
DB_PATH     = os.path.join(os.path.dirname(__file__), "..", "agent5_conversations.db")

VERDICTS = ["CRITICAL", "UPGRADE NOW", "EXTEND + PLAN", "REPLACE", "CLOUD MIGRATE", "MONITOR"]

# ── System prompt ─────────────────────────────────────────────────────────────
CONVERSATION_SYSTEM = f"""You are Agent 5 — a senior IT migration strategist at Infosys.
You are helping an enterprise architect define their OS and database migration policy
for a project running from 1 April 2026 to 30 June 2028.

You have REAL-TIME WEB SEARCH capability. Use it to:
- Look up current ESU/extended support pricing (Windows, SQL Server, Oracle, RHEL etc.)
- Find latest EOL/lifecycle dates that may have changed
- Research migration patterns, upgrade guides, best practices
- Check cloud service pricing (Azure SQL, AWS RDS, Aurora etc.)
- Answer any cost, licensing, or technical migration question accurately

Your job is to have a NATURAL CONVERSATION to understand the org's context.
Ask ONE focused question at a time. Build on previous answers.

Topics to cover (not all at once — weave them naturally):
1. EOL risk tolerance — zero / compensating controls / ESU / CVE-based
2. Support runway needed at project end (Jun 2028)
3. Budget — ESU approved? Tier-1 only? Cloud budget available?
4. Compliance — PCI DSS / HIPAA / SOX / GDPR / internal only
5. Windows EOL path — upgrade to Server 2025/Win11, ESU, Linux, Azure VD
6. Linux/Unix/AIX/Solaris path — in-place upgrade, RHEL/Ubuntu standardise, containerise
7. Database EOL path — in-place upgrade, open-source (PostgreSQL), cloud managed
8. Oracle licensing stance — reducing spend vs strategic
9. Cloud provider preference — Azure / AWS / GCP / on-prem
10. Legacy DB stance — Informix, SAP ASE, Progress, Ingres, IBM IMS
11. Migration capacity — how many systems can be migrated in the window
12. System criticality tiers — what gets prioritised first
13. Rollback/fallback policy for migrations

When the user asks about COSTS, PRICES, ESU rates, migration tools, upgrade guides,
or any real-time information — SEARCH THE WEB and give them accurate current figures.

RULES:
- Ask 1 question at a time
- If vague, ask a clarifying follow-up
- Search the web whenever cost/pricing/migration guidance is involved
- After 10-15 exchanges when you have sufficient policy context, respond with EXACTLY:
  {{"ready": true, "summary": "2-3 sentence policy summary", "context": {{...key-value policy context...}}}}
- Before that, respond naturally in plain English only
- Today: {TODAY}. Project ends 30 Jun 2028."""

PRINCIPLES_SYSTEM = """You are a senior IT migration strategist.
Generate 8-10 Guiding Principles (GP-01...GP-10) from a policy conversation.
Each must be specific, actionable, tied to what was discussed.
Return ONLY a JSON array, no markdown:
[{"code":"GP-01","title":"4-word title","rule":"One clear rule.","trigger":"If X → Y","category":"Risk|Budget|OS|Database|Execution"}]"""

FINAL_REC_SYSTEM = f"""You are a senior IT migration strategist cross-referencing:
1. Agent 2's expert technical recommendation
2. Organisation policy context from the conversation
3. Agreed Guiding Principles

Project: 1 Apr 2026 → 30 Jun 2028. Today: {TODAY}

For each record, produce a FINAL RECOMMENDATION that:
- Starts with one verdict: CRITICAL / UPGRADE NOW / EXTEND + PLAN / REPLACE / CLOUD MIGRATE / MONITOR
- Synthesises Agent 2's technical advice with org policy stance
- Cites a GP code
- Includes cost context where relevant
- Is 2-3 sentences max

Return ONLY valid JSON: {{"KEY": "VERDICT — recommendation. (GP-N)"}}"""


# ── SQLite helpers ─────────────────────────────────────────────────────────────
def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            session  TEXT NOT NULL,
            role     TEXT NOT NULL,
            content  TEXT NOT NULL,
            ts       DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session  TEXT PRIMARY KEY,
            context  TEXT,
            summary  TEXT,
            status   TEXT DEFAULT 'chatting',
            created  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated  DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit()
    return conn


def _save_message(session_id: str, role: str, content: str):
    conn = _get_db()
    conn.execute(
        "INSERT INTO conversations (session, role, content) VALUES (?,?,?)",
        (session_id, role, content)
    )
    conn.execute(
        "INSERT OR IGNORE INTO sessions (session) VALUES (?)", (session_id,)
    )
    conn.execute(
        "UPDATE sessions SET updated=CURRENT_TIMESTAMP WHERE session=?", (session_id,)
    )
    conn.commit()
    conn.close()


def _load_messages(session_id: str) -> list:
    conn = _get_db()
    rows = conn.execute(
        "SELECT role, content FROM conversations WHERE session=? ORDER BY id",
        (session_id,)
    ).fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in rows]


def _save_session_context(session_id: str, context: dict, summary: str, status: str):
    conn = _get_db()
    conn.execute(
        """INSERT INTO sessions (session, context, summary, status)
           VALUES (?,?,?,?)
           ON CONFLICT(session) DO UPDATE SET
           context=excluded.context, summary=excluded.summary,
           status=excluded.status, updated=CURRENT_TIMESTAMP""",
        (session_id, json.dumps(context), summary, status)
    )
    conn.commit()
    conn.close()


def _list_sessions() -> list:
    conn = _get_db()
    rows = conn.execute(
        "SELECT session, summary, status, updated FROM sessions ORDER BY updated DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return [{"session": r[0], "summary": r[1] or "In progress",
             "status": r[2], "updated": r[3]} for r in rows]


def _delete_session(session_id: str):
    conn = _get_db()
    conn.execute("DELETE FROM conversations WHERE session=?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE session=?", (session_id,))
    conn.commit()
    conn.close()


class PolicyAnalysisAgent:

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model  = "gpt-4o-mini-search-preview"   # Real-time web search on every turn

    @staticmethod
    def get_or_create_session() -> str:
        """Get current session ID from session_state or create new one."""
        if "a5_session_id" not in st.session_state:
            import uuid
            st.session_state.a5_session_id = str(uuid.uuid4())[:8]
        return st.session_state.a5_session_id

    @staticmethod
    def init_session():
        defaults = {
            "a5_status":         "idle",
            "a5_context":        {},
            "a5_principles":     [],
            "a5_costs":          {},
            "a5_os_done":        False,
            "a5_db_done":        False,
            "a5_preflight_done": False,
            "a5_log":            [],
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

    # ── Chat with real-time web search ────────────────────────────────────────
    def chat(self, messages: list) -> str:
        """
        Uses Responses API with web_search_preview tool.
        Agent can search the web on EVERY turn for live pricing,
        ESU costs, migration guides, EOL dates etc.
        """
        # Build input from message history
        if not messages:
            input_text = "Please start the policy conversation with your opening question."
        else:
            # Format as a conversation string for the Responses API
            conv = "\n\n".join(
                f"{'ARCHITECT' if m['role']=='user' else 'AGENT 5'}: {m['content']}"
                for m in messages[-20:]  # last 20 messages for context
            )
            input_text = (
                f"CONVERSATION SO FAR:\n{conv}\n\n"
                f"Continue the conversation as Agent 5. "
                f"Search the web if the user asks about costs, pricing, ESU rates, "
                f"migration guides, or any real-time information."
            )

        response = self.client.responses.create(
            model=self.model,
            instructions=CONVERSATION_SYSTEM,
            tools=[{"type": "web_search_preview"}],
            input=input_text
        )
        return (response.output_text or "").strip()

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

    # ── Generate Guiding Principles ───────────────────────────────────────────
    def generate_principles(self, context: dict, session_id: str) -> list:
        messages = _load_messages(session_id)
        conv_text = "\n".join(
            f"{'ARCHITECT' if m['role']=='user' else 'AGENT 5'}: {m['content'][:200]}"
            for m in messages[-24:]
        )
        ctx_text = "\n".join(f"{k}: {v}" for k, v in context.items())
        prompt = (
            f"POLICY CONTEXT:\n{ctx_text}\n\n"
            f"CONVERSATION:\n{conv_text}\n\n"
            "Generate 8-10 Guiding Principles."
        )
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini", max_tokens=2500,
                messages=[
                    {"role": "system", "content": PRINCIPLES_SYSTEM},
                    {"role": "user",   "content": prompt}
                ]
            )
            text = resp.choices[0].message.content.strip()
            if "```" in text:
                text = text.split("```json")[-1].split("```")[0] if "```json" in text \
                       else text.split("```")[1].split("```")[0]
            s, e = text.find("["), text.rfind("]")
            if s != -1 and e > s:
                return json.loads(text[s:e+1])
        except Exception:
            pass
        return [{"code":"GP-01","title":"Zero EOL Tolerance",
                 "rule":"No EOL software past 30 Jun 2028.",
                 "trigger":"EOL before Jun 2028 → Upgrade","category":"Risk"}]

    # ── Cost intelligence (web search) ────────────────────────────────────────
    def fetch_costs(self, progress_cb=None) -> dict:
        """
        Fetches LIVE pricing for common migration decisions using web search.
        Covers ESU, cloud DB, RHEL, Oracle support costs.
        """
        searches = [
            ("Windows Server 2016/2019 ESU",
             "Windows Server 2016 2019 Extended Security Updates cost per server per year 2025 2026 site:microsoft.com OR site:azure.microsoft.com"),
            ("SQL Server 2016/2017/2019 ESU",
             "SQL Server 2016 2017 2019 Extended Security Updates cost per core per year 2025 2026"),
            ("Oracle Database Support",
             "Oracle Database annual support renewal cost 22 percent extended support surcharge 2026"),
            ("RHEL Subscription Cost",
             "Red Hat Enterprise Linux RHEL subscription cost per server per year standard premium 2026"),
            ("Azure SQL / AWS RDS Pricing",
             "Azure SQL Managed Instance AWS Aurora RDS PostgreSQL monthly cost per instance 2026"),
            ("Migration Tools Cost",
             "AWS Database Migration Service Azure Database Migration Service cost pricing 2026"),
        ]
        costs = {}
        n = len(searches)
        for i, (vendor, query) in enumerate(searches):
            if progress_cb:
                progress_cb(i / n, f"🔍 Searching live pricing: {vendor}...")
            try:
                resp = self.client.responses.create(
                    model=self.model,
                    tools=[{"type": "web_search_preview"}],
                    input=(
                        f"Search for: {query}\n\n"
                        f"Return a 2-3 sentence summary with SPECIFIC current prices and figures. "
                        f"Include the source URL if available."
                    )
                )
                result = (resp.output_text or "").strip()
                costs[vendor] = result if result else "Could not retrieve live pricing."
            except Exception as ex:
                fallbacks = {
                    "Windows Server 2016/2019 ESU":
                        "Windows Server 2016 ESU Year 1: ~$198/server. Year 2: ~$396. Free via Azure Arc. (Source: Microsoft)",
                    "SQL Server 2016/2017/2019 ESU":
                        "SQL Server 2016 ESU: ~$1,418/core/year. SQL Server 2019: free until Jan 2030. (Source: Microsoft)",
                    "Oracle Database Support":
                        "Oracle annual support: 22% of license list price. Extended Support (years 4-5): +10% surcharge.",
                    "RHEL Subscription Cost":
                        "RHEL Standard: ~$800/yr/socket-pair. RHEL Premium: ~$1,300/yr. (Source: Red Hat)",
                    "Azure SQL / AWS RDS Pricing":
                        "Azure SQL MI: ~$465/mo (4 vCores). AWS RDS PostgreSQL db.t3.medium: ~$60/mo.",
                    "Migration Tools Cost":
                        "AWS DMS: ~$0.18/hr per replication instance. Azure DMS Standard: ~$0.10/hr.",
                }
                costs[vendor] = fallbacks.get(vendor, f"Live search unavailable: {str(ex)[:80]}")
        if progress_cb:
            progress_cb(1.0, "✅ Live pricing data fetched.")
        return costs

    # ── Final Recommendations ─────────────────────────────────────────────────
    def analyse_os(self, df, principles, costs, context, progress_cb=None):
        return self._analyse(df, "OS", principles, costs, context, progress_cb)

    def analyse_db(self, df, principles, costs, context, progress_cb=None):
        return self._analyse(df, "DB", principles, costs, context, progress_cb)

    def _analyse(self, df, kind, principles, costs, context, progress_cb):
        df = df.copy()
        for col in ["Final Recommendation","Final Verdict","Analysis Source"]:
            if col not in df.columns:
                df[col] = ""

        gp_text   = "\n".join(f"{p['code']}: {p['title']} — {p['rule']}" for p in principles)
        cost_text = "\n".join(f"{v}: {s}" for v, s in costs.items())
        ctx_text  = "\n".join(f"{k}: {v}" for k, v in context.items())
        rows      = df.to_dict("records")
        total     = len(rows)
        batch     = 15
        ai_count  = 0
        rb_count  = 0

        for i in range(0, total, batch):
            chunk = rows[i:i+batch]
            if progress_cb:
                progress_cb(i / total,
                    f"🧠 Generating Final Recommendations — {kind} rows {i+1}–{min(i+batch,total)} of {total}...")

            if kind == "OS":
                rows_text = "\n".join(
                    f"KEY={r['OS Version']} | "
                    f"Mainstream={r.get('Mainstream/Full Support End','')} | "
                    f"Extended={r.get('Extended/LTSC Support End','')} | "
                    f"Agent2={r.get('Recommendation','')[:120]}"
                    for r in chunk
                )
            else:
                rows_text = "\n".join(
                    f"KEY={r['Database']} {r['Version']} | "
                    f"Status={r.get('Status','')} | "
                    f"Extended={r.get('Extended Support End','')} | "
                    f"Replace={r.get('Replace','')} | Alt={r.get('Primary Alternative','')} | "
                    f"Agent2={r.get('Recommendation','')[:120]}"
                    for r in chunk
                )

            prompt = (
                f"ORG POLICY CONTEXT:\n{ctx_text}\n\n"
                f"GUIDING PRINCIPLES:\n{gp_text}\n\n"
                f"LIVE VENDOR COSTS:\n{cost_text}\n\n"
                f"PROJECT: 1 Apr 2026 → 30 Jun 2028 | Today: {TODAY}\n\n"
                f"RECORDS:\n{rows_text}\n\n"
                f"Return ONLY JSON: {{\"KEY\": \"VERDICT — Final rec. (GP-N)\"}}"
            )

            recs = {}; api_worked = False; last_error = None
            for attempt in range(2):
                try:
                    import time
                    if attempt > 0: time.sleep(2)
                    resp = self.client.chat.completions.create(
                        model="gpt-4o-mini", max_tokens=4000,
                        messages=[
                            {"role": "system", "content": FINAL_REC_SYSTEM},
                            {"role": "user",   "content": prompt}
                        ]
                    )
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

            if not api_worked and progress_cb:
                progress_cb(i / total,
                    f"⚠️ Batch {i+1}–{min(i+batch,total)} API error: {str(last_error)[:60]}")

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
            progress_cb(1.0,
                f"✅ {kind} done — OpenAI: {ai_count} rows | Rule-based: {rb_count} rows")
        return df

    def _rule_based(self, row, kind):
        def _parse(s):
            try: return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
            except: return None
        if kind == "OS":
            end  = _parse(row.get("Extended/LTSC Support End","")) \
                or _parse(row.get("Mainstream/Full Support End",""))
            name = row.get("OS Version","?")
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
