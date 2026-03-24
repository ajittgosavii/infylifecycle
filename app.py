"""
INFY Migration Version Lifecycle Tracker
5-Agent Streamlit Application — Infosys Enterprise Architecture

Core design:
- baseline_data.py holds ALL 321 OS/DB rows from Claude's training knowledge
- Data is visible IMMEDIATELY on app load — no waiting for Agent 1
- Agent 1 checks internet for date changes and updates Notes column
- Agent 2 fills Recommendation column via Claude AI
- Agent 3 refreshes every 14 days with permission
- Agent 4 snapshots data before every refresh
- Agent 5 interactive policy analysis → guiding principles → verdicts

Project window: Apr 2026 → Jun 2028
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os, types, importlib.util

# ── Python 3.14 Streamlit Cloud safe loader ───────────────────────────────────
_HERE = os.path.abspath(os.path.dirname(__file__))

def _load(dotted_name: str, rel_path: str):
    cached = sys.modules.get(dotted_name)
    if cached is not None and getattr(cached, "__file__", None):
        return cached
    abs_path = os.path.join(_HERE, rel_path)
    spec     = importlib.util.spec_from_file_location(dotted_name, abs_path)
    mod      = importlib.util.module_from_spec(spec)
    mod.__file__ = abs_path
    sys.modules[dotted_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(dotted_name, None)
        raise
    return mod

for _pkg in ("agents", "utils"):
    if _pkg not in sys.modules:
        _ns = types.ModuleType(_pkg)
        _ns.__path__ = [os.path.join(_HERE, _pkg)]
        _ns.__package__ = _pkg
        sys.modules[_pkg] = _ns

_m_baseline  = _load("baseline_data",         "baseline_data.py")
_m_os        = _load("agents.agent_os",        "agents/agent_os.py")
_m_db        = _load("agents.agent_db",        "agents/agent_db.py")
_m_refresh   = _load("agents.agent_refresh",   "agents/agent_refresh.py")
_m_version   = _load("agents.agent_versioning","agents/agent_versioning.py")
_m_analysis  = _load("agents.agent_analysis",  "agents/agent_analysis.py")
_m_export    = _load("utils.excel_export",     "utils/excel_export.py")

OSDataAgent          = _m_os.OSDataAgent
RecommendationAgent  = _m_db.RecommendationAgent
RefreshAgent         = _m_refresh.RefreshAgent
VersionGuardianAgent = _m_version.VersionGuardianAgent
PolicyAnalysisAgent  = _m_analysis.PolicyAnalysisAgent
export_to_excel      = _m_export.export_to_excel
OS_DATA              = _m_baseline.OS_DATA
DB_DATA              = _m_baseline.DB_DATA
OS_COLUMNS           = _m_baseline.OS_COLUMNS
DB_COLUMNS           = _m_baseline.DB_COLUMNS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="INFY Version Lifecycle Tracker",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "INFY Migration Version Lifecycle Tracker — Powered by Claude AI (Anthropic)"}
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.infy-header {
    background: linear-gradient(135deg, #001F5B 0%, #003087 60%, #0057C8 100%);
    padding: 1.2rem 2rem; border-radius: 12px;
    color: white; margin-bottom: 1.5rem;
}
.infy-header h1 { margin: 0; font-size: 1.55rem; font-weight: 700; }
.infy-header p  { margin: 4px 0 0; font-size: 0.82rem; opacity: 0.8; }
.agent-card {
    border-left: 4px solid; border-radius: 0 8px 8px 0;
    padding: 0.7rem 1rem; margin-bottom: 0.65rem;
    background: rgba(0,0,0,0.025);
}
.a1{border-color:#0EA5E9;} .a2{border-color:#8B5CF6;}
.a3{border-color:#F59E0B;} .a4{border-color:#10B981;} .a5{border-color:#7C3AED;}
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
}
.b-idle    { background:#F1F5F9; color:#64748B; }
.b-running { background:#FEF3C7; color:#92400E; }
.b-done    { background:#D1FAE5; color:#065F46; }
.b-error   { background:#FEE2E2; color:#991B1B; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    defaults = {
        # Load baseline data immediately — visible before Agent 1 runs
        "os_df":         pd.DataFrame(OS_DATA),
        "db_df":         pd.DataFrame(DB_DATA),
        "last_refresh":  None,
        "a1_status":     "idle",
        "a2_status":     "idle",
        "changes_log":   [],
        "old_os_df":     None,
        "old_db_df":     None,
        "a3_skip_until": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()
refresh_agent = RefreshAgent()
VersionGuardianAgent.init_session()
PolicyAnalysisAgent.init_session()


def badge(status: str) -> str:
    icons = {"idle":"◌","running":"⟳","done":"✓","error":"✕"}
    cls   = {"idle":"idle","running":"running","done":"done","error":"error"}.get(status,"idle")
    return f'<span class="badge b-{cls}">{icons.get(cls,"·")} {status.upper()}</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Infosys_logo.svg/1200px-Infosys_logo.svg.png", width=130)
    except Exception:
        st.markdown("### INFY")
    st.divider()

    st.subheader("🔑 Anthropic API Key")
    api_key = st.text_input("Enter your API key", type="password", placeholder="sk-ant-...",
                             help="Set ANTHROPIC_API_KEY in Streamlit Cloud Secrets.")
    if not api_key:
        try: api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception: pass

    key_ok = bool(api_key and api_key.startswith("sk-ant"))
    if api_key and not key_ok: st.error("⚠️ Key must start with sk-ant-")
    elif key_ok: st.success("✅ API key ready")
    st.divider()

    # Agent 1
    s1 = st.session_state.a1_status
    st.markdown(f"""<div class="agent-card a1">
    <b>🔍 Agent 1 — Internet Change Checker</b><br>{badge(s1)}
    <small style="display:block;margin-top:4px;color:#666">
    Checks internet for lifecycle date changes.<br>
    Data pre-loaded from Claude knowledge base<br>
    ({len(OS_DATA)} OS + {len(DB_DATA)} DB = {len(OS_DATA)+len(DB_DATA)} entries)</small>
    </div>""", unsafe_allow_html=True)
    run_a1 = st.button("▶ Run Agent 1 — Check for Updates", width="stretch", disabled=not key_ok)
    st.caption("⏱ ~2–3 min (16 targeted web checks)")
    st.divider()

    # Agent 2
    s2 = st.session_state.a2_status
    st.markdown(f"""<div class="agent-card a2">
    <b>🤖 Agent 2 — Recommendation Engine</b><br>{badge(s2)}
    <small style="display:block;margin-top:4px;color:#666">
    Claude AI fills Recommendation column for all rows</small>
    </div>""", unsafe_allow_html=True)
    run_a2 = st.button("▶ Run Agent 2 — Generate Recommendations", width="stretch", disabled=not key_ok)
    st.divider()

    # Agent 3
    st.markdown("""<div class="agent-card a3">
    <b>🔄 Agent 3 — Refresh Monitor</b>
    <small style="display:block;margin-top:4px;color:#666">
    14-day schedule · seeks permission before re-running</small>
    </div>""", unsafe_allow_html=True)
    refresh_agent.render_status_card(
        st.session_state.last_refresh,
        os_count=len(st.session_state.os_df),
        db_count=len(st.session_state.db_df)
    )
    st.divider()

    # Agent 4 / 5
    history = VersionGuardianAgent.get_history()
    a5s = st.session_state.get("a5_status", "idle")
    st.markdown(f"""<div class="agent-card a4">
    <b>🛡️ Agent 4 — Version Guardian</b>
    <small style="display:block;margin-top:4px;color:#666">{len(history)} snapshot(s)</small></div>
    <div class="agent-card a5">
    <b>🧠 Agent 5 — Policy Analysis</b><br>{badge(a5s)}
    <small style="display:block;margin-top:4px;color:#666">Apr 2026 → Jun 2028</small>
    </div>""", unsafe_allow_html=True)
    st.divider()

    os_recs = (st.session_state.os_df["Recommendation"] != "").sum()
    db_recs = (st.session_state.db_df["Recommendation"] != "").sum()
    st.caption(f"📊 OS: **{len(st.session_state.os_df)}** · DB: **{len(st.session_state.db_df)}** rows")
    st.caption(f"💡 Recommendations: OS {os_recs} · DB {db_recs}")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="infy-header">
  <h1>🖥️ INFY Migration Version Lifecycle Tracker</h1>
  <p>Infosys Enterprise Architecture &nbsp;·&nbsp;
     Powered by Claude AI (Anthropic) &nbsp;·&nbsp;
     Pre-loaded: 149 OS versions + 172 DB versions from Claude knowledge base &nbsp;·&nbsp;
     Agent 1 verifies date changes from the internet &nbsp;·&nbsp;
     Project: Apr 2026 → Jun 2028</p>
</div>
""", unsafe_allow_html=True)


# ── Agent 3 refresh banner ────────────────────────────────────────────────────
skip_until = st.session_state.get("a3_skip_until")
skip_active = skip_until and datetime.now() < skip_until

if (refresh_agent.is_refresh_due(st.session_state.last_refresh)
        and not skip_active and key_ok):
    approved = refresh_agent.render_refresh_banner(
        st.session_state.last_refresh,
        os_count=len(st.session_state.os_df),
        db_count=len(st.session_state.db_df)
    )
    if approved:
        VersionGuardianAgent.snapshot(
            st.session_state.os_df,
            st.session_state.db_df,
            st.session_state.changes_log
        )
        st.session_state.a1_status = "idle"
        st.session_state.a2_status = "idle"
        st.session_state.a5_os_done = False
        st.session_state.a5_db_done = False
        st.toast("✅ Refresh approved — click 'Run Agent 1' to check for updates.", icon="🔄")


# ── Run Agent 1 ────────────────────────────────────────────────────────────────
if run_a1:
    st.session_state.a1_status = "running"
    if not st.session_state.os_df.empty:
        VersionGuardianAgent.snapshot(
            st.session_state.os_df,
            st.session_state.db_df,
            st.session_state.changes_log
        )
    st.session_state.old_os_df = st.session_state.os_df.copy()
    st.session_state.old_db_df = st.session_state.db_df.copy()

    agent1 = OSDataAgent(api_key=api_key)

    st.info("🔍 **Agent 1** is checking the internet for lifecycle date changes. "
            "Baseline data ({} OS + {} DB) already loaded — this only looks for updates.".format(
            len(OS_DATA), len(DB_DATA)))

    prog   = st.progress(0, text="Starting internet checks...")
    status = st.empty()

    def a1_cb(pct, msg):
        prog.progress(min(pct, 1.0), text=msg)
        status.caption(msg)

    try:
        updates = agent1.fetch_updates(progress_callback=a1_cb)
        new_os, new_db, changes = agent1.merge_updates_into_df(
            st.session_state.os_df,
            st.session_state.db_df,
            updates
        )
        st.session_state.os_df     = new_os
        st.session_state.db_df     = new_db
        st.session_state.changes_log = changes
        st.session_state.last_refresh = datetime.now()
        st.session_state.a1_status    = "done"
        st.session_state.a5_os_done   = False
        st.session_state.a5_db_done   = False

        if changes:
            st.success(f"✅ **Agent 1 complete!** Found **{len(changes)} date changes** from the internet.")
            for c in changes[:10]:
                st.markdown(f"  - {c}")
        else:
            st.success("✅ **Agent 1 complete!** No date changes found — baseline data is current.")

    except Exception as e:
        st.session_state.a1_status = "error"
        st.error(f"❌ Agent 1 error: {e}")

    st.rerun()


# ── Run Agent 2 ────────────────────────────────────────────────────────────────
if run_a2:
    st.session_state.a2_status = "running"
    agent2 = RecommendationAgent(api_key=api_key)

    os_prog = st.progress(0, text="Agent 2: generating OS recommendations...")
    os_stat = st.empty()
    def a2_os_cb(pct, msg):
        os_prog.progress(min(pct,1.0), text=msg)
        os_stat.caption(msg)

    try:
        new_os = agent2.generate_os_recommendations(st.session_state.os_df, progress_callback=a2_os_cb)
        st.session_state.os_df = new_os
    except Exception as e:
        st.error(f"❌ OS recommendation error: {e}")
        st.session_state.a2_status = "error"

    db_prog = st.progress(0, text="Agent 2: generating DB recommendations...")
    db_stat = st.empty()
    def a2_db_cb(pct, msg):
        db_prog.progress(min(pct,1.0), text=msg)
        db_stat.caption(msg)

    try:
        new_db = agent2.generate_db_recommendations(st.session_state.db_df, progress_callback=a2_db_cb)
        st.session_state.db_df = new_db
    except Exception as e:
        st.error(f"❌ DB recommendation error: {e}")
        st.session_state.a2_status = "error"

    if st.session_state.a2_status != "error":
        st.session_state.a2_status = "done"
        os_filled = (st.session_state.os_df["Recommendation"] != "").sum()
        db_filled = (st.session_state.db_df["Recommendation"] != "").sum()
        if st.session_state.last_refresh is None:
            st.session_state.last_refresh = datetime.now()
        st.success(f"✅ **Agent 2 complete!** Recommendations for "
                   f"**{os_filled} OS** and **{db_filled} DB** entries.")
    st.rerun()


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_os, tab_db, tab_status, tab_history, tab_a5 = st.tabs([
    "🖥️ OS Versions", "🗄️ DB Versions",
    "📋 Agent Status & Log", "🛡️ Version History",
    "🧠 Agent 5 — Policy Analysis"
])


# ────────────────── Tab 1: OS Versions ────────────────────────────────────────
with tab_os:
    os_df = st.session_state.os_df

    m1, m2, m3, m4, m5 = st.columns(5)

    def is_eol(row):
        for col in ["Extended/LTSC Support End", "Mainstream/Full Support End"]:
            v = str(row.get(col, ""))
            if any(k in v.lower() for k in ["ended", "end of"]):
                return True
            if len(v) == 10 and v[0].isdigit():
                try:
                    from datetime import datetime as dt
                    return dt.strptime(v, "%Y-%m-%d") < dt.now()
                except Exception:
                    pass
        return False

    eol_count  = sum(1 for _, r in os_df.iterrows() if is_eol(r))
    upg_count  = (os_df.get("Upgrade",  pd.Series(dtype=str)) == "Y").sum()
    repl_count = (os_df.get("Replace",  pd.Series(dtype=str)) == "Y").sum()
    rec_count  = (os_df["Recommendation"] != "").sum()

    with m1: st.metric("Total OS Entries",   len(os_df))
    with m2: st.metric("⚠️ EOL / Expired",   int(eol_count))
    with m3: st.metric("⬆️ Upgrade Flagged", int(upg_count))
    with m4: st.metric("🔁 Replace Flagged", int(repl_count))
    with m5: st.metric("💡 Recommendations", int(rec_count))

    with st.expander("🔍 Filters", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            families = ["All"] + sorted(set(
                v.split()[0] for v in os_df["OS Version"].dropna() if v and not v.startswith("[")
            ))
            fam_f = st.selectbox("OS Family", families)
        with fc2: upg_f  = st.selectbox("Upgrade", ["All","Y","N"])
        with fc3: repl_f = st.selectbox("Replace", ["All","Y","N"])
        with fc4: rec_f  = st.selectbox("Has Recommendation", ["All","Yes","No"])

    view = os_df.copy()
    if fam_f  != "All": view = view[view["OS Version"].str.startswith(fam_f, na=False)]
    if upg_f  != "All": view = view[view.get("Upgrade", pd.Series(dtype=str)) == upg_f]
    if repl_f != "All": view = view[view.get("Replace", pd.Series(dtype=str)) == repl_f]
    if rec_f  == "Yes": view = view[view["Recommendation"] != ""]
    if rec_f  == "No":  view = view[view["Recommendation"] == ""]

    disp = {
        "OS Version":                    st.column_config.TextColumn("OS Version",        width=220),
        "Availability Date":             st.column_config.TextColumn("Available",         width=110),
        "Security/Standard Support End": st.column_config.TextColumn("Security End",      width=120),
        "Mainstream/Full Support End":   st.column_config.TextColumn("Mainstream End",    width=140),
        "Extended/LTSC Support End":     st.column_config.TextColumn("Extended End",      width=120),
        "Notes":                         st.column_config.TextColumn("Notes",             width=160),
        "Recommendation":                st.column_config.TextColumn("💡 Recommendation", width=380),
        "Upgrade":                       st.column_config.TextColumn("⬆ Upgrade",         width=80),
        "Replace":                       st.column_config.TextColumn("🔁 Replace",        width=80),
        "Primary Alternative":           st.column_config.TextColumn("Primary Alt",       width=160),
    }
    if "Policy Recommendation" in view.columns:
        disp["Policy Recommendation"] = st.column_config.TextColumn("🏛️ Policy Rec", width=360)
    if "Verdict" in view.columns:
        disp["Verdict"] = st.column_config.TextColumn("Verdict", width=120)

    st.caption(f"Showing {len(view)} of {len(os_df)} OS entries")
    st.dataframe(view, width="stretch", height=520, hide_index=True, column_config=disp)


# ────────────────── Tab 2: DB Versions ────────────────────────────────────────
with tab_db:
    db_df = st.session_state.db_df

    dm1, dm2, dm3, dm4, dm5 = st.columns(5)
    eol_db = (db_df.get("Status", pd.Series(dtype=str)).str.lower() == "end of life").sum()
    exp_db = (db_df.get("Status", pd.Series(dtype=str)).str.lower() == "expiring soon").sum()
    sup_db = (db_df.get("Status", pd.Series(dtype=str)).str.lower() == "supported").sum()
    rec_db = (db_df["Recommendation"] != "").sum()

    with dm1: st.metric("Total DB Entries",   len(db_df))
    with dm2: st.metric("🔴 End of Life",     int(eol_db))
    with dm3: st.metric("🟡 Expiring Soon",   int(exp_db))
    with dm4: st.metric("🟢 Supported",       int(sup_db))
    with dm5: st.metric("💡 Recommendations", int(rec_db))

    with st.expander("🔍 Filters", expanded=False):
        df1, df2, df3, df4 = st.columns(4)
        with df1:
            dbs = ["All"] + sorted(db_df["Database"].dropna().unique().tolist())
            db_f = st.selectbox("Database", dbs)
        with df2:
            types_ = ["All"] + sorted(db_df["Type"].dropna().unique().tolist())
            type_f = st.selectbox("Type", types_)
        with df3:
            statuses = ["All"] + sorted(db_df["Status"].dropna().unique().tolist())
            stat_f = st.selectbox("Status", statuses)
        with df4:
            repl_db_f = st.selectbox("Replace", ["All","Y","N"], key="repl_db")

    view_db = db_df.copy()
    if db_f      != "All": view_db = view_db[view_db["Database"] == db_f]
    if type_f    != "All": view_db = view_db[view_db["Type"]     == type_f]
    if stat_f    != "All": view_db = view_db[view_db["Status"]   == stat_f]
    if repl_db_f != "All": view_db = view_db[view_db.get("Replace", pd.Series(dtype=str)) == repl_db_f]

    def _style_status(val):
        m = {"end of life":   "background-color:#FFCDD2;color:#B71C1C",
             "expiring soon": "background-color:#FFE0B2;color:#E65100",
             "supported":     "background-color:#C8E6C9;color:#1B5E20",
             "future":        "background-color:#E3F2FD;color:#0D47A1"}
        return m.get(str(val).lower(), "")

    db_disp = {
        "Database":                st.column_config.TextColumn("Database",        width=180),
        "Version":                 st.column_config.TextColumn("Version",         width=120),
        "Type":                    st.column_config.TextColumn("Type",            width=150),
        "Mainstream / Premier End":st.column_config.TextColumn("Mainstream End",  width=130),
        "Extended Support End":    st.column_config.TextColumn("Extended End",    width=120),
        "Status":                  st.column_config.TextColumn("Status",          width=120),
        "Notes":                   st.column_config.TextColumn("Notes",           width=180),
        "Recommendation":          st.column_config.TextColumn("💡 Recommendation",width=360),
        "Upgrade":                 st.column_config.TextColumn("⬆ Upgrade",       width=80),
        "Replace":                 st.column_config.TextColumn("🔁 Replace",      width=80),
        "Primary Alternative":     st.column_config.TextColumn("Primary Alt",     width=150),
    }
    if "Policy Recommendation" in view_db.columns:
        db_disp["Policy Recommendation"] = st.column_config.TextColumn("🏛️ Policy Rec", width=360)
    if "Verdict" in view_db.columns:
        db_disp["Verdict"] = st.column_config.TextColumn("Verdict", width=120)

    st.caption(f"Showing {len(view_db)} of {len(db_df)} DB entries")
    st.dataframe(
        view_db.style.map(_style_status, subset=["Status"]) if "Status" in view_db.columns else view_db,
        width="stretch", height=520, hide_index=True, column_config=db_disp
    )


# ────────────────── Tab 3: Agent Status ───────────────────────────────────────
with tab_status:
    st.subheader("🤖 Agent Activity Dashboard")
    ca1, ca2, ca3 = st.columns(3)

    s1 = st.session_state.a1_status
    with ca1:
        icon1 = {"idle":"⚪","running":"🔵","done":"✅","error":"❌"}.get(s1,"⚪")
        st.markdown(f"""**{icon1} Agent 1 — Internet Change Checker**
- Status: `{s1.upper()}`
- Baseline: **{len(OS_DATA)} OS + {len(DB_DATA)} DB** rows pre-loaded from Claude knowledge
- Task: Checks internet for lifecycle date changes only
- Tool: claude-sonnet-4-6 + web\\_search (16 targeted checks)
- Updates: Notes column with [Web verified: date]""")

    s2 = st.session_state.a2_status
    with ca2:
        icon2 = {"idle":"⚪","running":"🔵","done":"✅","error":"❌"}.get(s2,"⚪")
        st.markdown(f"""**{icon2} Agent 2 — Recommendation Engine**
- Status: `{s2.upper()}`
- Tool: claude-haiku-4-5-20251001 (cost-efficient)
- Batch: 20 rows per API call
- Rules: EOL→CRITICAL, Expiring→URGENT, Supported→PLAN
- Oracle: flags PostgreSQL migration savings""")

    with ca3:
        last_r   = st.session_state.last_refresh
        days_left= refresh_agent.days_until_refresh(last_r)
        due      = refresh_agent.is_refresh_due(last_r)
        icon3    = "🟡" if due else ("✅" if last_r else "⚪")
        last_str = last_r.strftime("%d %b %Y %H:%M") if last_r else "Never"
        st.markdown(f"""**{icon3} Agent 3 — Refresh Monitor**
- Status: `{"REFRESH DUE" if due else ("MONITORING" if last_r else "WAITING")}`
- Interval: Every 14 days
- Last check: {last_str}
- Next check: {f"In {days_left} days" if last_r else "After first Agent 1 run"}""")

    st.divider()
    ca4, ca5 = st.columns(2)
    with ca4:
        h = VersionGuardianAgent.get_history()
        st.markdown(f"""**🛡️ Agent 4 — Version Guardian**
- Snapshots: **{len(h)}** stored
- Auto-runs before every Agent 1 refresh
- Preserves Recommendation + Policy columns
- Max 10 versions in session""")
    with ca5:
        a5s = st.session_state.get("a5_status","idle")
        gps = st.session_state.get("a5_principles",[])
        st.markdown(f"""**🧠 Agent 5 — Policy Analysis**
- Status: `{a5s.upper()}`
- Principles generated: **{len(gps)}**
- Project: 1 Apr 2026 → 30 Jun 2028
- Phases: Interview → Principles → Cost Intel → Verdicts""")

    if st.session_state.changes_log:
        st.divider()
        st.subheader(f"📋 Change Log — Last Agent 1 Run ({len(st.session_state.changes_log)} changes)")
        for c in st.session_state.changes_log:
            st.markdown(f"- {c}")
    else:
        st.info("No internet changes detected yet. Run Agent 1 to check for updates.")

    st.divider()
    st.subheader("📖 How to Use")
    st.markdown(f"""
**Data is pre-loaded** — {len(OS_DATA)} OS versions and {len(DB_DATA)} DB versions are visible immediately from Claude's knowledge base.

1. **Enter your Anthropic API key** in the sidebar (or add `ANTHROPIC_API_KEY` to Streamlit Cloud Secrets)
2. **Run Agent 2** — Claude AI fills expert recommendations for all {len(OS_DATA)+len(DB_DATA)} rows (recommended first step)
3. **Run Agent 1** — checks internet for any date changes since the baseline was created
4. **Run Agent 5** (Policy Analysis tab) — policy interview → guiding principles → migration verdicts
5. **Download Excel** — all data, colour-coded, with recommendations
6. **Agent 3** prompts you every 14 days to re-run Agent 1 and pick up any new changes
    """)


# ────────────────── Tab 4: Version History ────────────────────────────────────
with tab_history:
    st.subheader("🛡️ Agent 4 — Version History")
    VersionGuardianAgent.render_history_tab()


# ────────────────── Tab 5: Agent 5 Policy Analysis ────────────────────────────
with tab_a5:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
                padding:1.2rem 1.8rem;border-radius:12px;color:white;margin-bottom:1.5rem;">
      <h2 style="margin:0;font-size:1.3rem;font-weight:700;">
        🧠 Agent 5 — Policy Analysis &amp; Migration Intelligence
      </h2>
      <p style="margin:4px 0 0;font-size:0.8rem;opacity:0.8;">
        Project: <strong>1 Apr 2026 → 30 Jun 2028</strong> &nbsp;·&nbsp;
        Policy interview → Guiding principles → Live cost data → Policy recommendations
      </p>
    </div>""", unsafe_allow_html=True)

    if not key_ok:
        st.warning("⚠️ Enter your Anthropic API key in the sidebar to use Agent 5.")
    else:
        a5s = st.session_state.get("a5_status","idle")
        steps    = ["Policy Interview","Guiding Principles","Cost Intelligence","Analysis","Complete"]
        step_map = {"idle":0,"interviewing":1,"principles":1,"costing":2,"ready":2,"analysing":3,"done":4}
        cur_step = step_map.get(a5s, 0)
        cols5    = st.columns(5)
        for i, (col, lbl) in enumerate(zip(cols5, steps)):
            with col:
                if i < cur_step:
                    st.markdown(f"<div style='text-align:center;color:#10B981;font-size:0.75rem;'>✅<br>{lbl}</div>", unsafe_allow_html=True)
                elif i == cur_step:
                    st.markdown(f"<div style='text-align:center;color:#F59E0B;font-weight:600;font-size:0.75rem;'>● {lbl}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:center;color:#94A3B8;font-size:0.75rem;'>○<br>{lbl}</div>", unsafe_allow_html=True)
        st.divider()

        if a5s in ("idle","interviewing"):
            if a5s == "idle": st.session_state.a5_status = "interviewing"
            st.subheader("📋 Phase 1 — Organisation Policy Interview")
            st.caption("Answer 8 questions to define your migration policy.")
            answers = st.session_state.a5_answers
            PQS = _m_analysis.POLICY_QUESTIONS
            with st.form("policy_form"):
                for q in PQS:
                    st.markdown(f"**{q['id'].upper()}. {q['q']}**")
                    current = answers.get(q["key"], q["opts"][0])
                    idx_val = q["opts"].index(current) if current in q["opts"] else 0
                    choice  = st.radio(q["id"], q["opts"], index=idx_val,
                                       label_visibility="collapsed", key=f"pq_{q['key']}")
                    answers[q["key"]] = choice
                    st.markdown("")
                submitted = st.form_submit_button("✅ Submit → Generate Guiding Principles",
                                                   type="primary", width="stretch")
            if submitted:
                st.session_state.a5_answers = answers
                st.session_state.a5_status  = "principles"
                st.rerun()

        elif a5s == "principles":
            st.subheader("⚖️ Phase 2 — Generating Guiding Principles...")
            with st.spinner("Claude is generating guiding principles..."):
                agent5 = PolicyAnalysisAgent(api_key=api_key)
                principles = agent5.generate_principles(st.session_state.a5_answers)
                st.session_state.a5_principles = principles
                st.session_state.a5_status     = "costing"
            st.rerun()

        elif a5s == "costing":
            st.subheader("💰 Phase 3 — Fetching Vendor Cost Data...")
            prog5 = st.progress(0, text="Searching vendor costs...")
            stat5 = st.empty()
            def cost_cb(pct, msg):
                prog5.progress(min(pct,1.0), text=msg)
                stat5.caption(msg)
            agent5 = PolicyAnalysisAgent(api_key=api_key)
            costs  = agent5.fetch_costs(progress_cb=cost_cb)
            st.session_state.a5_costs  = costs
            st.session_state.a5_status = "ready"
            st.rerun()

        elif a5s == "ready":
            principles = st.session_state.a5_principles
            with st.expander(f"⚖️ Guiding Principles ({len(principles)})", expanded=True):
                c1, c2 = st.columns(2)
                for i, gp in enumerate(principles):
                    with (c1 if i%2==0 else c2):
                        st.markdown(
                            f"<div style='border-left:3px solid #3B82F6;padding:8px 12px;"
                            f"border-radius:0 6px 6px 0;background:rgba(59,130,246,0.06);margin-bottom:8px;'>"
                            f"<strong>{gp.get('code','?')}: {gp.get('title','?')}</strong><br>"
                            f"<span style='font-size:0.82rem;'>{gp.get('rule','')}</span><br>"
                            f"<span style='font-size:0.75rem;color:#6B7280;'>Trigger: {gp.get('trigger','')}</span></div>",
                            unsafe_allow_html=True)
            costs = st.session_state.a5_costs
            with st.expander(f"💰 Vendor Cost Intelligence ({len(costs)} sources)", expanded=False):
                for vendor, summary in costs.items():
                    st.markdown(f"**{vendor}:** {summary}")
            st.divider()
            st.subheader("🚀 Phase 4 — Run Policy Analysis")
            a2_os = (st.session_state.os_df["Recommendation"] != "").sum()
            a2_db = (st.session_state.db_df["Recommendation"] != "").sum()
            if a2_os + a2_db == 0:
                st.warning("⚠️ Recommended: Run Agent 2 before Agent 5 for richer context.")
            else:
                st.success(f"✅ Agent 2 recommendations available ({a2_os} OS + {a2_db} DB).")
            st.info(f"Ready to analyse all {len(st.session_state.os_df)+len(st.session_state.db_df)} entries against {len(principles)} guiding principles.")
            if st.button("▶ Run Agent 5 — Full Policy Analysis", type="primary", width="stretch"):
                st.session_state.a5_status = "analysing"
                st.rerun()
            if st.button("🔄 Restart Interview", width="stretch"):
                PolicyAnalysisAgent.reset()
                st.rerun()

        elif a5s == "analysing":
            st.subheader("🧠 Running Policy Analysis...")
            agent5     = PolicyAnalysisAgent(api_key=api_key)
            principles = st.session_state.a5_principles
            costs      = st.session_state.a5_costs
            if not st.session_state.get("a5_os_done"):
                p5 = st.progress(0, text="Analysing OS entries...")
                s5 = st.empty()
                def os5_cb(pct, msg): p5.progress(min(pct,1.0), text=msg); s5.caption(msg)
                st.session_state.os_df = agent5.analyse_os(st.session_state.os_df, principles, costs, os5_cb)
                st.session_state.a5_os_done = True
            if not st.session_state.get("a5_db_done"):
                p5b = st.progress(0, text="Analysing DB entries...")
                s5b = st.empty()
                def db5_cb(pct, msg): p5b.progress(min(pct,1.0), text=msg); s5b.caption(msg)
                st.session_state.db_df = agent5.analyse_db(st.session_state.db_df, principles, costs, db5_cb)
                st.session_state.a5_db_done = True
            st.session_state.a5_status = "done"
            st.rerun()

        elif a5s == "done":
            st.success("✅ **Agent 5 complete!** Policy Recommendation + Verdict columns added to both tabs.")
            verdicts = ["CRITICAL","UPGRADE NOW","EXTEND + PLAN","REPLACE","CLOUD MIGRATE","MONITOR"]
            os_df_now = st.session_state.os_df
            db_df_now = st.session_state.db_df
            if "Verdict" in os_df_now.columns or "Verdict" in db_df_now.columns:
                st.subheader("📊 Policy Verdict Summary")
                vcols = st.columns(6)
                for i, v in enumerate(verdicts):
                    os_c = int((os_df_now.get("Verdict", pd.Series(dtype=str)).str.upper().str.startswith(v.split()[0])).sum()) if "Verdict" in os_df_now.columns else 0
                    db_c = int((db_df_now.get("Verdict", pd.Series(dtype=str)).str.upper().str.startswith(v.split()[0])).sum()) if "Verdict" in db_df_now.columns else 0
                    with vcols[i]: st.metric(v, os_c+db_c, f"OS:{os_c} DB:{db_c}")
            if st.button("🔄 Re-run with New Policy", width="stretch"):
                PolicyAnalysisAgent.reset()
                st.rerun()


# ── Download Excel ─────────────────────────────────────────────────────────────
st.divider()
_, dl_col, _ = st.columns([1, 2, 1])
with dl_col:
    ts_str = datetime.now().strftime("%d %b %Y %H:%M UTC")
    excel_bytes = export_to_excel(
        st.session_state.os_df,
        st.session_state.db_df,
        generated_at=ts_str,
        principles=st.session_state.get("a5_principles", []),
        costs=st.session_state.get("a5_costs", {}),
        version_history=VersionGuardianAgent.get_history()
    )
    fname = f"INFY_Version_Tracker_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    os_n, db_n = len(st.session_state.os_df), len(st.session_state.db_df)
    st.download_button(
        label=f"📥 Download Excel — OS: {os_n} entries · DB: {db_n} entries",
        data=excel_bytes, file_name=fname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch", type="primary"
    )
    st.caption(f"📁 {fname} · Generated at {ts_str}")

st.markdown(
    "<p style='text-align:center;color:#94A3B8;font-size:0.72rem;margin-top:1.5rem;'>"
    "INFY Migration Reference Tracker · Infosys Enterprise Architecture · "
    "Powered by Claude AI (Anthropic) · claude-sonnet-4-6 (A1/A5) · claude-haiku-4-5-20251001 (A2) · "
    "All data from Claude knowledge base + internet verification</p>",
    unsafe_allow_html=True
)
