"""
Agent 5: Interactive Policy Analysis Agent
==========================================
Phase 1 — Policy Interview   : Chat-style UI asks 8 org policy questions
Phase 2 — Guiding Principles : Claude generates named GP-01..GP-N rules
Phase 3 — Cost Intelligence  : Live web search for vendor ESU/support costs
Phase 4 — Consolidated Analysis : Every OS/DB row scored → Policy Recommendation

Project window: 1 Apr 2026 → 30 Jun 2028
"""

import anthropic
import json
import pandas as pd
import streamlit as st
from datetime import datetime, date

# ── Project constants ────────────────────────────────────────────────────────
PROJECT_START = date(2026, 4, 1)
PROJECT_END   = date(2028, 6, 30)
TODAY         = date.today()

# ── Policy interview questions ────────────────────────────────────────────────
POLICY_QUESTIONS = [
    {
        "id": "q1",
        "question": "What is your organisation's risk tolerance for running **End-of-Life (EOL)** software during the migration project (Apr 2026 – Jun 2028)?",
        "options": [
            "Zero tolerance — all EOL software must be remediated before project end",
            "Low — EOL permitted only with compensating controls (WAF, IPS, isolation)",
            "Medium — EOL permitted if vendor ESU is purchased",
            "High — EOL acceptable if no known critical CVEs"
        ],
        "key": "eol_risk_tolerance"
    },
    {
        "id": "q2",
        "question": "What **minimum remaining support runway** is required for a product to be considered acceptable at project end (Jun 2028)?",
        "options": [
            "At least 24 months past Jun 2028 (i.e. supported until Jun 2030+)",
            "At least 12 months past Jun 2028 (i.e. supported until Jun 2029+)",
            "Active support on 30 Jun 2028 is sufficient",
            "No minimum — assessed case by case"
        ],
        "key": "min_support_runway"
    },
    {
        "id": "q3",
        "question": "Does your organisation have **budget approved** for Extended Security Updates (ESU) or paid vendor support extensions?",
        "options": [
            "Yes — ESU/extension budget is approved and available",
            "Limited — ESU available for Tier-1 critical systems only",
            "No — no budget for paid extensions; must upgrade or replace",
            "Under review — to be decided per system"
        ],
        "key": "esu_budget"
    },
    {
        "id": "q4",
        "question": "What is your organisation's **preferred remediation strategy** when a product reaches EOL?",
        "options": [
            "In-place upgrade to latest supported version (same vendor)",
            "Migration to open-source alternative (e.g. Oracle DB → PostgreSQL)",
            "Migration to cloud-managed service (e.g. on-prem SQL Server → Azure SQL)",
            "Hybrid — upgrade first, cloud-migrate in phase 2"
        ],
        "key": "remediation_strategy"
    },
    {
        "id": "q5",
        "question": "Are there **compliance/regulatory requirements** that govern your software lifecycle decisions?",
        "options": [
            "PCI DSS — payment card data in scope",
            "HIPAA — health data in scope",
            "SOX — financial systems in scope",
            "Multiple / internal policy only — no specific external regulation"
        ],
        "key": "compliance"
    },
    {
        "id": "q6",
        "question": "What is your organisation's stance on **Oracle licensing costs**? (Oracle DB, Oracle Linux, Oracle middleware)",
        "options": [
            "Actively seeking to reduce Oracle spend — OSS migration preferred",
            "Oracle spend acceptable if product is best-fit for requirements",
            "Oracle is strategic — expanding Oracle estate is acceptable",
            "Oracle to be evaluated case-by-case against alternatives"
        ],
        "key": "oracle_policy"
    },
    {
        "id": "q7",
        "question": "For **Windows OS**, what is your preferred path when a version reaches EOL within the project window?",
        "options": [
            "Upgrade to Windows 11 / Windows Server 2025 (latest supported)",
            "Purchase Microsoft ESU and plan upgrade post-project",
            "Migrate to Linux (RHEL / Ubuntu) where possible",
            "Evaluate Windows 365 / Azure Virtual Desktop for client OS"
        ],
        "key": "windows_policy"
    },
    {
        "id": "q8",
        "question": "How should the **cost analysis** influence the final recommendation?",
        "options": [
            "Cost is primary — cheapest compliant option wins",
            "Cost is important but security/compliance takes precedence",
            "TCO over 3 years is the metric — include migration effort",
            "Cost is a factor but strategic alignment is more important"
        ],
        "key": "cost_weighting"
    },
]

# ── Cost search targets ───────────────────────────────────────────────────────
COST_SEARCH_TARGETS = [
    {
        "vendor": "Microsoft Windows ESU",
        "query": "Microsoft Windows Server 2012 2016 Windows 10 Extended Security Updates ESU pricing cost per server device 2026",
        "hint": "Find per-server ESU pricing for Windows Server 2012 R2, 2016. Windows 10 ESU Year 1/2/3 per-device cost. Include Azure Arc free ESU benefit."
    },
    {
        "vendor": "Microsoft SQL Server ESU",
        "query": "Microsoft SQL Server 2012 2014 2016 Extended Security Updates ESU pricing cost per core 2026",
        "hint": "Find per-core annual ESU pricing for SQL Server 2012, 2014, 2016. Include Azure migration free ESU option and SQL Server 2022 upgrade licensing cost."
    },
    {
        "vendor": "Oracle Database Support",
        "query": "Oracle Database annual support renewal premier extended support pricing cost per processor 2026",
        "hint": "Find Oracle annual support cost (typically 22% of license). Include Extended Support surcharge 10-20%. Include Oracle to PostgreSQL migration cost savings estimate."
    },
    {
        "vendor": "Red Hat RHEL",
        "query": "Red Hat Enterprise Linux RHEL subscription pricing per server socket 2026 standard premium",
        "hint": "Find RHEL Standard (~$800/year) and Premium (~$1,300/year) subscription costs per socket-pair. Include RHEL for SAP pricing."
    },
    {
        "vendor": "IBM Db2 and AIX",
        "query": "IBM Db2 annual support subscription pricing IBM AIX maintenance cost per processor 2026",
        "hint": "Find IBM Db2 and IBM AIX annual support/maintenance pricing per processor or per PVU. Include IBM Passport Advantage pricing model."
    },
    {
        "vendor": "SAP HANA and SAP ASE",
        "query": "SAP HANA support maintenance annual pricing SAP Sybase ASE support cost 2026",
        "hint": "Find SAP HANA Enterprise Edition support cost and SAP ASE (Sybase) annual maintenance pricing. Include SAP S-user licensing model."
    },
    {
        "vendor": "Oracle MySQL and MariaDB",
        "query": "MySQL Enterprise Edition subscription pricing MariaDB Enterprise subscription cost 2026",
        "hint": "Find MySQL Enterprise Edition annual subscription cost per server. MariaDB Enterprise subscription pricing. Compare against free community editions."
    },
    {
        "vendor": "MongoDB Atlas and Enterprise",
        "query": "MongoDB Enterprise Advanced subscription pricing MongoDB Atlas cost per server 2026",
        "hint": "Find MongoDB Enterprise Advanced annual per-server cost. MongoDB Atlas pricing tiers. Include community vs enterprise cost comparison."
    },
    {
        "vendor": "Teradata Vantage",
        "query": "Teradata Vantage database annual support maintenance pricing cost 2026",
        "hint": "Find Teradata annual maintenance cost (typically 20-25% of license). Include Teradata Cloud Vantage pricing as migration option."
    },
    {
        "vendor": "Cloud Migration Costs",
        "query": "Azure SQL Managed Instance pricing AWS RDS PostgreSQL Google Cloud SQL annual cost per instance 2026",
        "hint": "Find representative annual costs for Azure SQL MI, AWS RDS PostgreSQL, and Google Cloud SQL as cloud migration targets. Include compute + storage estimates."
    },
]

# ── System prompts ────────────────────────────────────────────────────────────
PRINCIPLES_SYSTEM = f"""You are a senior enterprise IT strategy consultant at Infosys.
Today: {TODAY.strftime('%d %B %Y')}
Project window: 1 April 2026 → 30 June 2028

Based on the organisation's policy answers below, generate a concise set of named 
Guiding Principles (GP-01, GP-02, etc.) that will govern every migration decision.

Each principle must:
- Have a short code (GP-01)
- Have a clear title (5 words max)  
- Have a 1-sentence rule
- Include a Decision trigger (e.g. "If EOL before Jun 2028 → Upgrade")

Format as JSON array only (no markdown):
[
  {{"code":"GP-01","title":"Zero EOL Tolerance","rule":"...","trigger":"If EOL before 30 Jun 2028 → Upgrade immediately"}},
  ...
]"""

ANALYSIS_SYSTEM = f"""You are a senior enterprise migration architect at Infosys.
Today: {TODAY.strftime('%d %B %Y')}
Project window: 1 April 2026 → 30 June 2028

You will receive:
1. Guiding Principles (GP-01..GPn) derived from org policy
2. Live vendor cost data
3. A batch of OS or DB version records

For each record produce a Policy Recommendation using this exact format:
[VERDICT] Reason. Cost context. GP reference.

VERDICT must be one of:
- UPGRADE NOW    — EOL already or expiring within project window, upgrade is mandatory
- EXTEND + PLAN  — ESU/extension acceptable short-term, upgrade must start within project
- REPLACE        — Migrate to alternative product (OSS or cloud)
- CLOUD MIGRATE  — Move to cloud-managed equivalent
- MONITOR        — Supported past project end, no action needed now
- CRITICAL       — EOL already, no ESU available, immediate risk

Be specific: name the target version, cost figure if known, and cite GP code.
Return ONLY a JSON object mapping "key" → "policy_recommendation":
{{"key": "policy_recommendation_text", ...}}"""


class PolicyAnalysisAgent:
    """Agent 5 — Interactive Policy Analysis Agent."""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model  = "claude-opus-4-20250514"

    # ── Phase 1: Policy interview state ──────────────────────────────────────
    @staticmethod
    def init_session():
        defaults = {
            "a5_answers":     {},           # {question_key: answer_text}
            "a5_step":        0,            # current question index
            "a5_principles":  [],           # [{code, title, rule, trigger}]
            "a5_costs":       {},           # {vendor: cost_summary_text}
            "a5_status":      "idle",       # idle|interviewing|principles|costing|analysing|done
            "a5_chat":        [],           # [{role, content}] for display
            "a5_os_analysed": False,
            "a5_db_analysed": False,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    @staticmethod
    def reset():
        keys = ["a5_answers","a5_step","a5_principles","a5_costs",
                "a5_status","a5_chat","a5_os_analysed","a5_db_analysed"]
        for k in keys:
            if k in st.session_state:
                del st.session_state[k]
        PolicyAnalysisAgent.init_session()

    # ── Phase 2: Generate guiding principles ─────────────────────────────────
    def generate_principles(self, answers: dict) -> list:
        answers_text = "\n".join(
            f"Q: {q['question'].replace('**','')}\nA: {answers.get(q['key'], 'Not answered')}"
            for q in POLICY_QUESTIONS
        )
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=PRINCIPLES_SYSTEM,
                messages=[{"role": "user",
                           "content": f"Organisation policy answers:\n\n{answers_text}"}]
            )
            text = resp.content[0].text.strip()
            for fence in ("```json","```"):
                if fence in text:
                    text = text.split(fence,1)[-1].split("```",1)[0].strip()
            return json.loads(text)
        except Exception as e:
            return [{"code":"GP-01","title":"Error generating","rule":str(e),"trigger":""}]

    # ── Phase 3: Fetch live vendor costs ─────────────────────────────────────
    def fetch_costs(self, progress_cb=None) -> dict:
        costs = {}
        total = len(COST_SEARCH_TARGETS)
        for idx, target in enumerate(COST_SEARCH_TARGETS):
            if progress_cb:
                progress_cb(idx/total, f"Fetching cost data: {target['vendor']}...")
            try:
                prompt = (
                    f"Search for current pricing/cost information: {target['query']}\n"
                    f"Focus: {target['hint']}\n"
                    f"Return a 2-3 sentence plain-text cost summary with specific figures where found. "
                    f"Today: {TODAY.strftime('%d %B %Y')}"
                )
                resp = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    tools=[{"type": "web_search_20250305", "name": "web_search"}],
                    messages=[{"role": "user", "content": prompt}]
                )
                text = "".join(
                    b.text for b in resp.content if hasattr(b, "text")
                ).strip()
                costs[target["vendor"]] = text or "Cost data not available."
            except Exception as e:
                costs[target["vendor"]] = f"Could not retrieve: {e}"
            if progress_cb:
                progress_cb((idx+1)/total, f"✅ {target['vendor']} cost data retrieved")
        return costs

    # ── Phase 4: Analyse OS rows ──────────────────────────────────────────────
    def analyse_os(self, df: pd.DataFrame, principles: list,
                   costs: dict, progress_cb=None) -> pd.DataFrame:
        df = df.copy()
        if "Policy Recommendation" not in df.columns:
            df["Policy Recommendation"] = ""
        if "Verdict" not in df.columns:
            df["Verdict"] = ""

        rows = df.to_dict("records")
        batch_size = 15
        total = len(rows)

        gp_text   = self._principles_text(principles)
        cost_text = self._costs_text(costs)

        for i in range(0, total, batch_size):
            batch = rows[i:i+batch_size]
            if progress_cb:
                progress_cb(i/total,
                    f"🧠 Agent 5 analysing OS rows {i+1}–{min(i+batch_size,total)} of {total}...")
            recs = self._analyse_batch(batch, "OS", gp_text, cost_text)
            for idx, row in df.iloc[i:i+batch_size].iterrows():
                key = row["OS Version"]
                if key in recs:
                    rec  = recs[key]
                    verdict = rec.split()[0] if rec else ""
                    df.at[idx, "Policy Recommendation"] = rec
                    df.at[idx, "Verdict"] = verdict

        if progress_cb:
            progress_cb(1.0, f"✅ OS policy analysis complete — {total} rows")
        return df

    # ── Phase 4: Analyse DB rows ──────────────────────────────────────────────
    def analyse_db(self, df: pd.DataFrame, principles: list,
                   costs: dict, progress_cb=None) -> pd.DataFrame:
        df = df.copy()
        if "Policy Recommendation" not in df.columns:
            df["Policy Recommendation"] = ""
        if "Verdict" not in df.columns:
            df["Verdict"] = ""

        rows = df.to_dict("records")
        batch_size = 15
        total = len(rows)

        gp_text   = self._principles_text(principles)
        cost_text = self._costs_text(costs)

        for i in range(0, total, batch_size):
            batch = rows[i:i+batch_size]
            if progress_cb:
                progress_cb(i/total,
                    f"🧠 Agent 5 analysing DB rows {i+1}–{min(i+batch_size,total)} of {total}...")
            recs = self._analyse_batch(batch, "DB", gp_text, cost_text)
            for idx, row in df.iloc[i:i+batch_size].iterrows():
                key = f"{row['Database']} {row['Version']}"
                if key in recs:
                    rec = recs[key]
                    verdict = rec.split()[0] if rec else ""
                    df.at[idx, "Policy Recommendation"] = rec
                    df.at[idx, "Verdict"] = verdict

        if progress_cb:
            progress_cb(1.0, f"✅ DB policy analysis complete — {total} rows")
        return df

    # ── Internal ──────────────────────────────────────────────────────────────
    def _analyse_batch(self, batch: list, kind: str,
                       gp_text: str, cost_text: str) -> dict:
        if kind == "OS":
            rows_text = "\n".join(
                f"- KEY={r.get('OS Version','?')} | "
                f"Mainstream End={r.get('Mainstream/Full Support End','')} | "
                f"Extended End={r.get('Extended/LTSC Support End','')} | "
                f"Security End={r.get('Security/Standard Support End','')} | "
                f"Upgrade={r.get('Upgrade','')} | Replace={r.get('Replace','')} | "
                f"Agent2 Rec={r.get('Recommendation','')[:80]}"
                for r in batch
            )
            key_fn = lambda r: r.get("OS Version", "")
        else:
            rows_text = "\n".join(
                f"- KEY={r.get('Database','?')} {r.get('Version','?')} | "
                f"Status={r.get('Status','')} | "
                f"Mainstream End={r.get('Mainstream / Premier End','')} | "
                f"Extended End={r.get('Extended Support End','')} | "
                f"Replace={r.get('Replace','')} | Alt={r.get('Primary Alternative','')} | "
                f"Agent2 Rec={r.get('Recommendation','')[:80]}"
                for r in batch
            )
            key_fn = lambda r: f"{r.get('Database','?')} {r.get('Version','?')}"

        user_msg = (
            f"GUIDING PRINCIPLES:\n{gp_text}\n\n"
            f"LIVE VENDOR COSTS:\n{cost_text}\n\n"
            f"PROJECT WINDOW: 1 Apr 2026 → 30 Jun 2028\n\n"
            f"RECORDS TO ANALYSE:\n{rows_text}\n\n"
            f"Return JSON mapping each KEY value to its Policy Recommendation."
        )

        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=ANALYSIS_SYSTEM,
                messages=[{"role": "user", "content": user_msg}]
            )
            text = resp.content[0].text.strip()
            for fence in ("```json","```"):
                if fence in text:
                    text = text.split(fence,1)[-1].split("```",1)[0].strip()
            return json.loads(text)
        except Exception:
            return {key_fn(r): self._rule_based(r, kind) for r in batch}

    def _rule_based(self, row: dict, kind: str) -> str:
        """Fallback rule-based analysis when API fails."""
        def parse(s):
            if not s or not isinstance(s, str): return None
            try: return datetime.strptime(s[:10], "%Y-%m-%d").date()
            except: return None

        if kind == "OS":
            end = parse(row.get("Extended/LTSC Support End","")) or \
                  parse(row.get("Mainstream/Full Support End",""))
            name = row.get("OS Version","?")
        else:
            end = parse(row.get("Extended Support End","")) or \
                  parse(row.get("Mainstream / Premier End",""))
            name = f"{row.get('Database','?')} {row.get('Version','?')}"

        if not end:
            return "MONITOR — Support dates unclear; verify manually. (GP-02)"
        if end < TODAY:
            return f"CRITICAL — {name} already EOL. Immediate action required. (GP-01)"
        if end < PROJECT_END:
            return f"UPGRADE NOW — {name} support ends {end} before project end Jun 2028. (GP-01)"
        if end < date(2030, 6, 30):
            return f"EXTEND + PLAN — {name} supported until {end}. Plan upgrade within project. (GP-02)"
        return f"MONITOR — {name} supported until {end}, past project end. No action now. (GP-05)"

    @staticmethod
    def _principles_text(principles: list) -> str:
        if not principles:
            return "No guiding principles defined yet."
        return "\n".join(
            f"{p.get('code','?')}: {p.get('title','?')} — {p.get('rule','?')} | Trigger: {p.get('trigger','')}"
            for p in principles
        )

    @staticmethod
    def _costs_text(costs: dict) -> str:
        if not costs:
            return "No cost data fetched yet."
        return "\n".join(f"{vendor}: {summary}" for vendor, summary in costs.items())


# ── Streamlit UI renderer ─────────────────────────────────────────────────────

def render_agent5_tab(agent5: PolicyAnalysisAgent, key_ok: bool):
    """Full Agent 5 UI rendered inside its Streamlit tab."""

    PolicyAnalysisAgent.init_session()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
                padding:1.2rem 1.8rem;border-radius:12px;color:white;margin-bottom:1.5rem;">
      <h2 style="margin:0;font-size:1.3rem;font-weight:700;">
        🧠 Agent 5 — Policy Analysis &amp; Migration Intelligence
      </h2>
      <p style="margin:4px 0 0;font-size:0.8rem;opacity:0.8;">
        Project window: <strong>1 Apr 2026 → 30 Jun 2028</strong> &nbsp;·&nbsp;
        Interactive policy interview → Guiding principles → Live cost intelligence → 
        Consolidated policy recommendations
      </p>
    </div>
    """, unsafe_allow_html=True)

    status = st.session_state.a5_status

    # ── Progress stepper ──────────────────────────────────────────────────────
    steps = ["Policy Interview", "Guiding Principles", "Cost Intelligence", "Analysis", "Complete"]
    step_map = {"idle":0,"interviewing":1,"principles":2,"costing":2,"analysing":3,"done":4}
    current_step = step_map.get(status, 0)

    cols = st.columns(5)
    for i, (col, label) in enumerate(zip(cols, steps)):
        with col:
            if i < current_step:
                st.markdown(f"<div style='text-align:center;color:#10B981;font-size:0.75rem;'>✅<br>{label}</div>",
                            unsafe_allow_html=True)
            elif i == current_step:
                st.markdown(f"<div style='text-align:center;color:#F59E0B;font-weight:600;font-size:0.75rem;'>● {label}</div>",
                            unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center;color:#94A3B8;font-size:0.75rem;'>○<br>{label}</div>",
                            unsafe_allow_html=True)

    st.divider()

    # ── Phase 1: Policy Interview ─────────────────────────────────────────────
    if status in ("idle", "interviewing"):
        st.subheader("📋 Phase 1 — Organisation Policy Interview")
        st.caption(
            "Agent 5 needs to understand your organisation's migration policy before it can "
            "generate guiding principles and analyse each OS/DB entry. "
            "Please answer the 8 questions below."
        )

        if status == "idle":
            st.session_state.a5_status = "interviewing"

        answers = st.session_state.a5_answers
        all_answered = True

        with st.form("policy_form"):
            for q in POLICY_QUESTIONS:
                st.markdown(f"**{q['id'].upper()}. {q['question']}**")
                current = answers.get(q["key"], q["options"][0])
                idx = q["options"].index(current) if current in q["options"] else 0
                choice = st.radio(
                    label=q["id"],
                    options=q["options"],
                    index=idx,
                    key=f"radio_{q['key']}",
                    label_visibility="collapsed"
                )
                answers[q["key"]] = choice
                st.markdown("")

            submitted = st.form_submit_button(
                "✅ Submit Policy Answers → Generate Guiding Principles",
                type="primary", width="stretch",
                disabled=not key_ok
            )

        if not key_ok:
            st.warning("⚠️ Enter your Anthropic API key in the sidebar to proceed.")

        if submitted:
            st.session_state.a5_answers  = answers
            st.session_state.a5_status   = "principles"
            st.rerun()

    # ── Phase 2: Generate Guiding Principles ──────────────────────────────────
    elif status == "principles":
        st.subheader("⚖️ Phase 2 — Generating Guiding Principles...")

        with st.spinner("Claude AI is analysing your policy answers and generating guiding principles..."):
            principles = agent5.generate_principles(st.session_state.a5_answers)
            st.session_state.a5_principles = principles
            st.session_state.a5_status     = "costing"

        st.rerun()

    # ── Phase 3: Cost Intelligence ────────────────────────────────────────────
    elif status == "costing":
        st.subheader("💰 Phase 3 — Fetching Live Vendor Cost Data...")

        prog = st.progress(0, text="Starting vendor cost search...")
        stat = st.empty()

        def cost_cb(pct, msg):
            prog.progress(min(pct, 1.0), text=msg)
            stat.caption(msg)

        costs = agent5.fetch_costs(progress_cb=cost_cb)
        st.session_state.a5_costs  = costs
        st.session_state.a5_status = "ready_to_analyse"
        st.rerun()

    # ── Ready to analyse ──────────────────────────────────────────────────────
    elif status == "ready_to_analyse":
        _render_principles_and_costs()

        st.divider()
        st.subheader("🚀 Phase 4 — Run Policy Analysis")

        os_empty = st.session_state.os_df.empty
        db_empty = st.session_state.db_df.empty
        os_recs  = (st.session_state.os_df.get("Recommendation", pd.Series(dtype=str)) != "").sum() \
                   if not os_empty else 0
        db_recs  = (st.session_state.db_df.get("Recommendation", pd.Series(dtype=str)) != "").sum() \
                   if not db_empty else 0
        total_rows = len(st.session_state.os_df) + len(st.session_state.db_df)
        recs_filled = os_recs + db_recs

        if os_empty and db_empty:
            st.warning("⚠️ No OS or DB data loaded yet. Run Agent 1 first, then come back to Agent 5.")
        else:
            # Agent 2 prerequisite check
            if recs_filled == 0:
                st.warning(
                    "⚠️ **Recommended: Run Agent 2 before Agent 5.** "
                    "Agent 5 uses Agent 2's recommendations as context for its policy analysis. "
                    "Running Agent 5 without Agent 2 will still work but the analysis will have less context."
                )
            elif recs_filled < total_rows * 0.5:
                st.info(
                    f"ℹ️ Agent 2 has filled {recs_filled}/{total_rows} recommendations. "
                    "You can proceed, or run Agent 2 first for fuller context."
                )
            else:
                st.success(
                    f"✅ Agent 2 recommendations available ({recs_filled}/{total_rows} rows). "
                    "Agent 5 will use these as context for its policy analysis."
                )

            st.info(
                f"Ready to analyse **{len(st.session_state.os_df)} OS entries** and "
                f"**{len(st.session_state.db_df)} DB entries** against your "
                f"{len(st.session_state.a5_principles)} guiding principles and live cost data."
            )
            if st.button("▶ Run Agent 5 — Full Policy Analysis",
                         type="primary", width="stretch"):
                st.session_state.a5_status = "analysing"
                st.rerun()

        col_reset, _ = st.columns([1, 3])
        with col_reset:
            if st.button("🔄 Restart Interview", width="stretch"):
                PolicyAnalysisAgent.reset()
                st.rerun()

    # ── Analysing ─────────────────────────────────────────────────────────────
    elif status == "analysing":
        st.subheader("🧠 Phase 4 — Running Policy Analysis...")

        principles = st.session_state.a5_principles
        costs      = st.session_state.a5_costs

        if not st.session_state.a5_os_analysed and not st.session_state.os_df.empty:
            os_prog = st.progress(0, text="Analysing OS entries...")
            os_stat = st.empty()
            def os_cb(pct, msg):
                os_prog.progress(min(pct,1.0), text=msg)
                os_stat.caption(msg)
            new_os = agent5.analyse_os(st.session_state.os_df, principles, costs, os_cb)
            st.session_state.os_df = new_os
            st.session_state.a5_os_analysed = True

        if not st.session_state.a5_db_analysed and not st.session_state.db_df.empty:
            db_prog = st.progress(0, text="Analysing DB entries...")
            db_stat = st.empty()
            def db_cb(pct, msg):
                db_prog.progress(min(pct,1.0), text=msg)
                db_stat.caption(msg)
            new_db = agent5.analyse_db(st.session_state.db_df, principles, costs, db_cb)
            st.session_state.db_df = new_db
            st.session_state.a5_db_analysed = True

        st.session_state.a5_status = "done"
        st.rerun()

    # ── Done: Results ─────────────────────────────────────────────────────────
    elif status == "done":
        st.success(
            "✅ **Agent 5 analysis complete!** "
            "The 'Policy Recommendation' and 'Verdict' columns have been added to both sheets. "
            "Download the updated Excel file using the button below."
        )

        _render_principles_and_costs()

        st.divider()
        _render_analysis_results()

        col_reset, _ = st.columns([1, 3])
        with col_reset:
            if st.button("🔄 Re-run Interview with New Policy", width="stretch"):
                PolicyAnalysisAgent.reset()
                st.rerun()


def _render_principles_and_costs():
    """Show generated guiding principles and cost summary."""
    principles = st.session_state.get("a5_principles", [])
    costs      = st.session_state.get("a5_costs", {})

    if principles:
        with st.expander(f"⚖️ Guiding Principles ({len(principles)} generated)", expanded=True):
            gp_cols = st.columns(2)
            for i, gp in enumerate(principles):
                with gp_cols[i % 2]:
                    st.markdown(
                        f"<div style='border-left:3px solid #3B82F6;padding:8px 12px;"
                        f"border-radius:0 6px 6px 0;background:rgba(59,130,246,0.06);"
                        f"margin-bottom:8px;'>"
                        f"<strong>{gp.get('code','?')}: {gp.get('title','?')}</strong><br>"
                        f"<span style='font-size:0.82rem;'>{gp.get('rule','')}</span><br>"
                        f"<span style='font-size:0.75rem;color:#6B7280;'>"
                        f"Trigger: {gp.get('trigger','')}</span></div>",
                        unsafe_allow_html=True
                    )

    if costs:
        with st.expander(f"💰 Live Vendor Cost Intelligence ({len(costs)} sources)", expanded=False):
            for vendor, summary in costs.items():
                st.markdown(f"**{vendor}**")
                st.caption(summary)
                st.markdown("")


def _render_analysis_results():
    """Show verdict summary and policy recommendation columns."""
    os_df = st.session_state.os_df
    db_df = st.session_state.db_df

    # Verdict colour map
    VERDICT_COLORS = {
        "CRITICAL":      "#FFCDD2",
        "UPGRADE":       "#FFE0B2",
        "EXTEND":        "#FFF9C4",
        "REPLACE":       "#E3F2FD",
        "CLOUD":         "#E8F5E9",
        "MONITOR":       "#F1F8E9",
    }

    def verdict_color(v):
        for k, c in VERDICT_COLORS.items():
            if str(v).upper().startswith(k):
                return f"background-color:{c}"
        return ""

    res_tab_os, res_tab_db = st.tabs(["🖥️ OS Policy Analysis", "🗄️ DB Policy Analysis"])

    with res_tab_os:
        if "Policy Recommendation" in os_df.columns:
            # Verdict summary metrics
            verdicts = os_df["Verdict"].value_counts() if "Verdict" in os_df.columns else pd.Series()
            vc = st.columns(6)
            labels = ["CRITICAL", "UPGRADE", "EXTEND", "REPLACE", "CLOUD", "MONITOR"]
            for i, lbl in enumerate(labels):
                count = sum(v for k, v in verdicts.items() if str(k).upper().startswith(lbl))
                with vc[i]:
                    st.metric(lbl, count)

            st.dataframe(
                os_df[["OS Version","Mainstream/Full Support End",
                        "Extended/LTSC Support End","Verdict",
                        "Policy Recommendation","Recommendation"]].style.map(
                    verdict_color, subset=["Verdict"]
                ),
                width="stretch", height=480, hide_index=True,
                column_config={
                    "OS Version":               st.column_config.TextColumn("OS Version",       width=200),
                    "Mainstream/Full Support End": st.column_config.TextColumn("Mainstream End",width=130),
                    "Extended/LTSC Support End":st.column_config.TextColumn("Extended End",     width=120),
                    "Verdict":                  st.column_config.TextColumn("Verdict",          width=110),
                    "Policy Recommendation":    st.column_config.TextColumn("🏛️ Policy Rec",   width=400),
                    "Recommendation":           st.column_config.TextColumn("Agent 2 Rec",      width=300),
                }
            )
        else:
            st.info("OS analysis not yet run.")

    with res_tab_db:
        if "Policy Recommendation" in db_df.columns:
            verdicts = db_df["Verdict"].value_counts() if "Verdict" in db_df.columns else pd.Series()
            vc2 = st.columns(6)
            for i, lbl in enumerate(labels):
                count = sum(v for k, v in verdicts.items() if str(k).upper().startswith(lbl))
                with vc2[i]:
                    st.metric(lbl, count)

            st.dataframe(
                db_df[["Database","Version","Status",
                        "Mainstream / Premier End","Extended Support End",
                        "Verdict","Policy Recommendation","Recommendation"]].style.map(
                    verdict_color, subset=["Verdict"]
                ),
                width="stretch", height=480, hide_index=True,
                column_config={
                    "Database":                 st.column_config.TextColumn("Database",         width=120),
                    "Version":                  st.column_config.TextColumn("Version",          width=90),
                    "Status":                   st.column_config.TextColumn("Status",           width=110),
                    "Mainstream / Premier End": st.column_config.TextColumn("Mainstream End",   width=130),
                    "Extended Support End":     st.column_config.TextColumn("Extended End",     width=120),
                    "Verdict":                  st.column_config.TextColumn("Verdict",          width=110),
                    "Policy Recommendation":    st.column_config.TextColumn("🏛️ Policy Rec",   width=400),
                    "Recommendation":           st.column_config.TextColumn("Agent 2 Rec",      width=300),
                }
            )
        else:
            st.info("DB analysis not yet run.")
