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

# ── OS Family Categorization ─────────────────────────────────────────────────
OS_FAMILY_RULES = [
    ("Windows Family",      ["Windows"],       "Desktop 10/11 & Server 2012–2025"),
    ("RHEL/Clone Family",   ["RHEL", "Red Hat", "AlmaLinux", "Alma", "Rocky", "Oracle Linux",
                             "CentOS", "CentOS Stream"],
                                               "RHEL, Alma, Rocky, Oracle Linux, CentOS"),
    ("Debian/Ubuntu Family", ["Ubuntu", "Debian"], "Ubuntu 14.04+ & Debian 8–13"),
    ("SUSE Family",         ["SLES", "SUSE", "openSUSE"], "SLES 11–16"),
    ("Legacy Unix",         ["AIX", "HP-UX", "Solaris", "Tru64"], "AIX, HP-UX, Solaris, Tru64"),
    ("BSD & VMS",           ["FreeBSD", "OpenBSD", "NetBSD", "OpenVMS"], "FreeBSD & OpenVMS"),
    ("Apple",               ["macOS", "iOS", "iPadOS"], "macOS 13–26"),
]

def categorize_os_families(os_df):
    """Categorize the OS dataframe into families. Returns dict: family_name → list of OS versions."""
    families = {}
    uncategorized = []
    for _, row in os_df.iterrows():
        ver = str(row.get("OS Version", ""))
        matched = False
        for fam_name, keywords, _ in OS_FAMILY_RULES:
            if any(kw.lower() in ver.lower() for kw in keywords):
                families.setdefault(fam_name, []).append(ver)
                matched = True
                break
        if not matched and ver:
            uncategorized.append(ver)
    # Add uncategorized to "Other" if any
    if uncategorized:
        families["Other"] = uncategorized
    return families

def get_family_display():
    """Return list of (family_name, description, emoji) for UI display."""
    return [
        ("Windows Family",       "Desktop 10/11 & Server 2012–2025", "🪟"),
        ("RHEL/Clone Family",    "RHEL, Alma, Rocky, Oracle Linux, CentOS", "🐧"),
        ("Debian/Ubuntu Family", "Ubuntu 14.04+ & Debian 8–13", "🐧"),
        ("SUSE Family",          "SLES 11–16", "🦎"),
        ("Legacy Unix",          "AIX, HP-UX, Solaris, Tru64", "🖥️"),
        ("BSD & VMS",            "FreeBSD & OpenVMS", "👾"),
        ("Apple",                "macOS 13–26", "🍎"),
        ("Other",                "Other OS not listed above", "❓"),
    ]

# ── OS Migration Guiding Principles (default knowledge base) ─────────────────
DEFAULT_OS_PRINCIPLES = {
    "Windows Family": {
        "cloud_map": {"Azure": "Azure / Azure Gov", "AWS": "AWS", "GCP": "GCP", "OCI": "OCI",
                       "GovCloud": "Azure Gov / AWS GovCloud", "_default": "Azure / Azure Gov"},
        "upgrade": "COTS: Upgrade to Server 2022/2025 to maintain vendor support and security compliance.",
        "replace":  "Custom: Replace Windows OS with Linux Containers (.NET Core) to eliminate license costs.",
    },
    "RHEL/Clone Family": {
        "cloud_map": {"AWS": "AWS / GovCloud", "Azure": "Azure", "GCP": "GCP", "OCI": "OCI",
                       "GovCloud": "AWS GovCloud", "_default": "AWS / GovCloud"},
        "upgrade": "COTS: Upgrade to RHEL 9.x or Oracle Linux 9.x as required by the software vendor's certification.",
        "replace":  "Custom: Replace legacy Linux with Amazon Linux 2023 to leverage AWS-native security and performance.",
    },
    "Debian/Ubuntu Family": {
        "cloud_map": {"GCP": "GCP / GDC", "AWS": "AWS", "Azure": "Azure", "OCI": "OCI",
                       "GovCloud": "GCP Assured Workloads", "_default": "GCP / GDC"},
        "upgrade": "COTS: Upgrade to the latest LTS (Long Term Support) version to ensure a stable 5-year security patch window.",
        "replace":  "Custom: Replace the standalone OS with Google Container-Optimized OS for microservices workloads.",
    },
    "SUSE Family": {
        "cloud_map": {"Azure": "Azure / AWS", "AWS": "Azure / AWS", "GCP": "GCP", "OCI": "OCI",
                       "GovCloud": "Azure Gov", "_default": "Azure / AWS"},
        "upgrade": "COTS: Upgrade to SLES 15 SP5+ specifically for SAP HANA or high-availability enterprise applications.",
        "replace":  "Custom: Replace manual SLES installs with Automated Cloud Images managed via SUSE Manager.",
    },
    "Legacy Unix": {
        "cloud_map": {"_default": "On-Prem / Bare Metal"},
        "upgrade": "None: No cloud upgrade path exists. Maintain \"As-Is\" on existing hardware with network isolation.",
        "replace":  "COTS/Custom: Mandatory Replacement. Transition the workload to Modern x86 Linux on the preferred cloud provider.",
    },
    "BSD & VMS": {
        "cloud_map": {"_default": "Specialized / Hybrid"},
        "upgrade": "COTS: Upgrade to the latest stable release branch supported by the hardware abstraction layer.",
        "replace":  "Custom: Replace with Hardened Linux Distributions to consolidate the technical skill set required for maintenance.",
    },
    "Apple": {
        "cloud_map": {"AWS": "AWS / Local", "Azure": "Azure", "GCP": "GCP",
                       "_default": "AWS / Local"},
        "upgrade": "Custom: Upgrade to the latest N-1 Version to ensure compatibility with modern developer toolchains (Xcode).",
        "replace":  "Custom: Replace physical on-prem hardware with Managed EC2 Mac Instances for cloud-based CI/CD.",
    },
}

PRINCIPLES_TABLE_SYSTEM = f"""You are Agent 5 — a senior IT migration strategist at Infosys.
Given the user's selected OS families and their chosen cloud provider, generate a guiding
principles table. For each OS family, provide:
- The best cloud target (considering the user's preference)
- An OS Upgrade Principle (for COTS/vendor-supported software)
- An OS Replacement Principle (for custom/modernized approaches)

Be specific, actionable, and reference actual product versions.
Return ONLY a JSON array:
[{{"os_family": "...", "cloud_target": "...", "upgrade_principle": "...", "replacement_principle": "..."}}]

Today: {TODAY}. Project ends 30 Jun 2028."""


def generate_principles_table(selected_families, cloud_name, cloud_key, agent=None):
    """
    Generate the guiding principles table.
    Uses defaults first, then optionally enhances with AI.
    Returns list of dicts with keys: os_family, cloud_target, upgrade_principle, replacement_principle.
    """
    rows = []
    for fam in selected_families:
        if fam == "Other":
            continue
        defaults = DEFAULT_OS_PRINCIPLES.get(fam)
        if defaults:
            cloud_map = defaults.get("cloud_map", {})
            cloud_target = cloud_map.get(cloud_key, cloud_map.get("_default", cloud_name))
            rows.append({
                "os_family": fam,
                "cloud_target": cloud_target,
                "upgrade_principle": defaults["upgrade"],
                "replacement_principle": defaults["replace"],
            })
        else:
            # Unknown family — provide generic
            rows.append({
                "os_family": fam,
                "cloud_target": cloud_name,
                "upgrade_principle": "Upgrade to the latest supported version to maintain vendor support.",
                "replacement_principle": "Evaluate containerization or cloud-native alternatives.",
            })

    # Optionally enhance with AI if agent provided
    if agent and rows:
        try:
            prompt = (
                f"User's selected OS families: {', '.join(selected_families)}\n"
                f"User's preferred cloud: {cloud_name}\n\n"
                f"Here are the default principles I've prepared:\n"
                + json.dumps(rows, indent=2) +
                f"\n\nReview and enhance these principles to be more specific to the "
                f"user's cloud choice ({cloud_name}). Keep the same structure but "
                f"make recommendations more tailored. Return ONLY the JSON array."
            )
            resp = agent.client.chat.completions.create(
                model=agent.model, max_tokens=2000,
                messages=[
                    {"role": "system", "content": PRINCIPLES_TABLE_SYSTEM},
                    {"role": "user", "content": prompt}
                ])
            text = resp.choices[0].message.content.strip()
            if "```" in text:
                text = text.split("```json")[-1].split("```")[0] if "```json" in text \
                       else text.split("```")[1].split("```")[0]
            s, e = text.find("["), text.rfind("]")
            if s != -1 and e > s:
                enhanced = json.loads(text[s:e+1])
                if enhanced and len(enhanced) == len(rows):
                    rows = enhanced
        except Exception:
            pass  # Keep defaults if AI fails

    return rows


LANDSCAPE_VERIFY_SYSTEM = """You are Agent 5 — a senior IT migration strategist.
The user says they have an OS that is not in our tracked list.
Your job is to determine:
1. Is the user referring to an OS we already track but by a different name/nickname?
   (e.g. "RHEL" = "Red Hat Enterprise Linux", "Win Server" = "Windows Server")
2. Is this a genuinely new OS that we should add to our tracking?

Our tracked OS families: Windows (10/11, Server 2003-2025), RHEL (7-10), Ubuntu (14.04-24.04),
Debian (8-13), SLES (11-16), CentOS/Stream, Rocky Linux, AlmaLinux, Oracle Linux,
macOS (Ventura/Sonoma/Sequoia), AIX (7.2-7.3), HP-UX (11i), Solaris (10-11.4),
Tru64, FreeBSD (13-14), OpenVMS, ChromeOS, Android, iOS/iPadOS, Fedora,
Raspberry Pi OS, IBM i.

Respond with ONLY this JSON:
{"match_found": true/false,
 "matched_to": "exact OS name from our list if match found, else null",
 "is_valid_os": true/false,
 "os_name": "the canonical name of the OS",
 "explanation": "brief explanation of your determination"
}"""

CONVERSATION_SYSTEM = f"""You are Agent 5 — a senior IT migration strategist at Infosys.
Help an enterprise architect define their OS and database migration policy
for a project running from 1 April 2026 to 30 June 2028.

YOUR APPROACH — BE ADAPTIVE:
- Some users will answer all questions in detail. Others will give a brief context statement
  and want to proceed quickly. BOTH are valid. Adapt to the user's pace.
- If the user gives a rich context upfront (e.g. "We are a large bank with PCI DSS scope,
  zero EOL tolerance, Azure preferred, small migration team"), extract as much as you can
  from that single message and ask only about the gaps.
- If the user says "just proceed" or "that's enough" or "go ahead" — respect that and signal ready.
- For any topics NOT discussed, apply sensible enterprise defaults in the context JSON.

TOPICS TO COVER (ask only what you still need):
1.  eol_tolerance  — Risk tolerance for EOL software (default if not asked: "Low — ESU with controls")
2.  min_runway     — Support runway at Jun 2028 (default: "12 months past project end")
3.  esu_budget     — ESU budget (default: "Limited — Tier-1 only")
4.  compliance     — Regulatory scope (default: "Internal policy only")
5.  windows_path   — Windows EOL path (default: "In-place upgrade to latest supported version")
6.  linux_path     — Linux/Unix/AIX path (default: "In-place upgrade same distro")
7.  db_eol_path    — Database EOL path (default: "In-place upgrade same vendor")
8.  oracle_stance  — Oracle licensing (default: "Evaluate case by case")
9.  cloud_provider — Cloud provider (default: "No strong preference")
10. legacy_db      — Legacy DBs stance (default: "Retain if stable, migrate if EOL in window")
11. capacity       — Migration capacity (default: "Medium — 20-30 systems in project window")
12. criticality    — System priority (default: "EOL-risk first, then compliance scope")
13. rollback       — Rollback policy (default: "Parallel run for Tier-1, in-place for others")

SIGNAL READY when:
- You have explicit or inferred answers for most topics, OR
- The user has indicated they want to proceed, OR
- You have had at least 4 exchanges and covered the most critical topics
  (eol_tolerance, compliance, windows_path, db_eol_path)

When ready, respond with ONLY this JSON:
{{"ready": true,
  "summary": "2-3 sentence org-specific policy summary based on what was discussed",
  "context": {{
    "eol_tolerance": "...", "min_runway": "...", "esu_budget": "...",
    "compliance": "...", "windows_path": "...", "linux_path": "...",
    "db_eol_path": "...", "oracle_stance": "...", "cloud_provider": "...",
    "legacy_db": "...", "capacity": "...", "criticality": "...", "rollback": "..."
  }},
  "inferred_topics": ["list of topics that used defaults, not explicitly discussed"]
}}
Today: {TODAY}. Project ends 30 Jun 2028."""

PRINCIPLES_SYSTEM = """You are a senior IT migration strategist.
Generate 8-10 Guiding Principles from a SPECIFIC policy conversation.

CRITICAL: Each principle must be ORG-SPECIFIC — use actual details from the conversation
(specific thresholds, budgets, compliance frameworks, named products, team sizes mentioned).
Generic principles like "Understand risk tolerance" are NOT acceptable.

Good example: GP-01: "PCI DSS Zero-EOL — All payment system OS/DB versions must be on
supported releases by 30 Jun 2028. No ESU permitted for Tier-1 PCI scope systems."
Bad example: GP-01: "Risk Tolerance — Understand organization's risk tolerance."

Return ONLY a JSON array:
[{"code":"GP-01","title":"4-word specific title","rule":"One specific actionable rule with named systems/dates/thresholds.",
  "trigger":"If [specific condition] → [specific action]","category":"Risk|Budget|OS|Database|Execution"}]"""

FINAL_REC_SYSTEM = f"""You are a senior IT migration strategist at Infosys.
Cross-reference:
1. Agent 2's expert technical recommendation
2. Organisation's specific policy context from the conversation
3. Agreed Guiding Principles (cite by code)

Project: 1 Apr 2026 → 30 Jun 2028. Today: {TODAY}.

For each record, produce a FINAL RECOMMENDATION that:
- Starts with: CRITICAL / UPGRADE NOW / EXTEND + PLAN / REPLACE / CLOUD MIGRATE / MONITOR
- Synthesises Agent 2's technical advice with the ORG'S SPECIFIC POLICY (not generic advice)
- Cites a GP code e.g. (GP-01)
- Is 2-3 sentences, specific to this record

Return ONLY valid JSON: {{"KEY": "VERDICT — org-specific recommendation. (GP-N)"}}"""


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
            "a5_ws_done": False, "a5_as_done": False, "a5_fw_done": False,
            "a5_preflight_done": False, "a5_log": [],
            "a5_landscape_families": {},
            "a5_landscape_selected": [],
            "a5_landscape_other_pending": False,
            "a5_custom_cloud_profiles": [],
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
                  "a5_costs","a5_os_done","a5_db_done",
                  "a5_ws_done","a5_as_done","a5_fw_done",
                  "a5_preflight_done","a5_log",
                  "a5_landscape_families","a5_landscape_selected",
                  "a5_landscape_other_pending","a5_custom_cloud_profiles",
                  "a5_principles_table_data"]:
            st.session_state.pop(k, None)
        PolicyAnalysisAgent.init_session()

    def verify_unknown_os(self, user_input: str, os_df) -> dict:
        """Check if user-described OS matches something we already track or is genuinely new."""
        known_os = ", ".join(os_df["OS Version"].unique().tolist()[:80])
        prompt = (f"The user says their environment includes: \"{user_input}\"\n\n"
                  f"Our currently tracked OS versions include (sample): {known_os}\n\n"
                  f"Is this an OS we already track (possibly by a different name), "
                  f"or is this genuinely a new OS we should add?")
        try:
            resp = self.client.chat.completions.create(
                model=self.model, max_tokens=300,
                messages=[
                    {"role": "system", "content": LANDSCAPE_VERIFY_SYSTEM},
                    {"role": "user", "content": prompt}
                ])
            text = resp.choices[0].message.content.strip()
            if "```" in text:
                text = text.split("```json")[-1].split("```")[0] if "```json" in text \
                       else text.split("```")[1].split("```")[0]
            s, e = text.find("{"), text.rfind("}")
            if s != -1 and e > s:
                return json.loads(text[s:e+1])
        except Exception:
            pass
        return {"match_found": False, "is_valid_os": False, "os_name": user_input,
                "explanation": "Could not verify — please add manually if needed."}

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

    def is_conversation_complete(self, reply: str, message_count: int = 0) -> tuple:
        """
        Accept ready signal adaptively:
        - Minimum 4 exchanges (8 messages) OR user explicitly said to proceed
        - Agent fills defaults for any uncovered topics — nothing is blocked
        Returns (done, context, summary, inferred_topics)
        """
        try:
            s, e = reply.find("{"), reply.rfind("}")
            if s != -1 and e > s:
                data = json.loads(reply[s:e+1])
                if data.get("ready"):
                    context         = data.get("context", {})
                    inferred        = data.get("inferred_topics", [])
                    summary         = data.get("summary", "")
                    # Only guard: need at least 4 exchanges (8 messages)
                    # so the agent has had a chance to ask something
                    if message_count < 8:
                        return False, {}, "", []
                    # Fill any completely missing keys with defaults
                    DEFAULTS = {
                        "eol_tolerance":  "Low — ESU with compensating controls",
                        "min_runway":     "12 months past Jun 2028",
                        "esu_budget":     "Limited — Tier-1 critical systems only",
                        "compliance":     "Internal policy only",
                        "windows_path":   "In-place upgrade to latest supported version",
                        "linux_path":     "In-place upgrade same distro",
                        "db_eol_path":    "In-place upgrade same vendor",
                        "oracle_stance":  "Evaluate Oracle vs alternatives case by case",
                        "cloud_provider": "No strong cloud preference",
                        "legacy_db":      "Retain if stable, migrate if EOL within project",
                        "capacity":       "Medium — 20-30 systems across project lifespan",
                        "criticality":    "EOL-risk first, then compliance scope",
                        "rollback":       "Parallel run for Tier-1, in-place for others",
                    }
                    for k, default in DEFAULTS.items():
                        if not context.get(k, "").strip():
                            context[k] = f"[Default] {default}"
                            if k not in inferred:
                                inferred.append(k)
                    return True, context, summary, inferred
        except Exception:
            pass
        return False, {}, "", []

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

    def analyse_ws(self, df, principles, costs, context, progress_cb=None):
        return self._analyse(df, "WS", principles, costs, context, progress_cb)

    def analyse_as(self, df, principles, costs, context, progress_cb=None):
        return self._analyse(df, "AS", principles, costs, context, progress_cb)

    def analyse_fw(self, df, principles, costs, context, progress_cb=None):
        return self._analyse(df, "FW", principles, costs, context, progress_cb)

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

            if kind == "OS":
                rows_text = "\n".join(
                    f"KEY={r['OS Version']} | Mainstream={r.get('Mainstream/Full Support End','')} | "
                    f"Extended={r.get('Extended/LTSC Support End','')} | "
                    f"Agent2={r.get('Recommendation','')[:120]}"
                    for r in chunk
                )
            else:
                # DB, WS, AS, FW all share same column structure
                name_col_map = {"DB": "Database", "WS": "Web Server", "AS": "App Server", "FW": "Framework"}
                name_col = name_col_map.get(kind, "Database")
                rows_text = "\n".join(
                    f"KEY={r.get(name_col,'?')} {r.get('Version','?')} | Status={r.get('Status','')} | "
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
                if kind == "OS":
                    key = row["OS Version"]
                else:
                    nc = {"DB": "Database", "WS": "Web Server", "AS": "App Server", "FW": "Framework"}.get(kind, "Database")
                    key = f"{row.get(nc, '?')} {row.get('Version', '')}".strip()
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
            # DB, WS, AS, FW all share same column structure
            end  = _parse(row.get("Extended Support End","")) \
                or _parse(row.get("Mainstream / Premier End",""))
            nc = {"DB": "Database", "WS": "Web Server", "AS": "App Server", "FW": "Framework"}.get(kind, "Database")
            name = f"{row.get(nc,'?')} {row.get('Version','?')}"
        if not end:
            return f"MONITOR — Verify support dates for {name}. (GP-02)"
        if end < TODAY:
            return f"CRITICAL — {name} EOL as of {end}. Immediate action required. (GP-01)"
        if end < PROJECT_END:
            return f"UPGRADE NOW — {name} ends {end}, before Jun 2028. Act now. (GP-01)"
        if end < date(2030, 6, 30):
            return f"EXTEND + PLAN — {name} until {end}. Plan upgrade within project. (GP-02)"
        return f"MONITOR — {name} until {end}, past project end. No immediate action. (GP-05)"
