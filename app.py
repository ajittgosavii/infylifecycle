"""
INFY Migration Version Lifecycle Tracker
Multi-Agent Streamlit Application — Infosys Enterprise Architecture

Agents:
  1 — Fetches ALL OS & DB lifecycle data live from the internet (no hardcoded data)
  2 — Generates expert AI recommendations per row via Claude AI
  3 — Bi-weekly refresh monitor with user permission dialog
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os, importlib.util, types

# ── Python 3.14 / Streamlit Cloud compatible imports ─────────────────────────
# Standard package imports break on Python 3.14 hot-reloads due to a stricter
# sys.modules KeyError. We load every local module directly from its file path
# using importlib.util.spec_from_file_location — this is independent of
# sys.path and never touches sys.modules for parent packages.

_HERE = os.path.abspath(os.path.dirname(__file__))

def _load(module_name: str, rel_path: str):
    """
    Load a module from an absolute path, cache in sys.modules only after
    successful execution. If a previously cached module has no useful attrs
    (broken partial load), re-execute it.
    """
    abs_path = os.path.join(_HERE, rel_path)

    # Check if already cached — but verify it's not a broken partial load
    if module_name in sys.modules:
        cached = sys.modules[module_name]
        # A properly loaded module will have __file__ set
        if getattr(cached, "__file__", None):
            return cached
        # Cached but broken — remove and reload
        del sys.modules[module_name]

    spec   = importlib.util.spec_from_file_location(module_name, abs_path)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = abs_path   # mark before exec so circular imports work
    try:
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception:
        # Remove broken module from cache so next attempt reloads cleanly
        sys.modules.pop(module_name, None)
        raise
    return module

# Ensure parent packages exist as empty namespace packages so sub-modules
# can import each other with relative-style names if needed
for _pkg in ("agents", "utils"):
    if _pkg not in sys.modules:
        _ns = types.ModuleType(_pkg)
        _ns.__path__ = [os.path.join(_HERE, _pkg)]
        _ns.__package__ = _pkg
        sys.modules[_pkg] = _ns

# Load each agent module explicitly
_m_os       = _load("agents.agent_os",        "agents/agent_os.py")
_m_db       = _load("agents.agent_db",        "agents/agent_db.py")
_m_refresh  = _load("agents.agent_refresh",   "agents/agent_refresh.py")
_m_version  = _load("agents.agent_versioning","agents/agent_versioning.py")
_m_analysis = _load("agents.agent_analysis",  "agents/agent_analysis.py")
_m_export   = _load("utils.excel_export",     "utils/excel_export.py")

# Bind names used throughout app.py
OSDataAgent          = _m_os.OSDataAgent
OS_COLUMNS           = _m_os.OS_COLUMNS
DB_COLUMNS           = _m_os.DB_COLUMNS
RecommendationAgent  = _m_db.RecommendationAgent
RefreshAgent         = _m_refresh.RefreshAgent
VersionGuardianAgent = _m_version.VersionGuardianAgent
PolicyAnalysisAgent  = _m_analysis.PolicyAnalysisAgent
render_agent5_tab    = _m_analysis.render_agent5_tab
export_to_excel      = _m_export.export_to_excel

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
.a1 { border-color: #0EA5E9; }
.a2 { border-color: #8B5CF6; }
.a3 { border-color: #F59E0B; }

.badge {
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
}
.b-idle    { background:#F1F5F9; color:#64748B; }
.b-running { background:#FEF3C7; color:#92400E; }
.b-done    { background:#D1FAE5; color:#065F46; }
.b-error   { background:#FEE2E2; color:#991B1B; }

.empty-state {
    text-align: center; padding: 4rem 2rem;
    color: #94A3B8; border: 2px dashed #E2E8F0;
    border-radius: 12px; margin: 1rem 0;
}
.empty-state h3 { color: #64748B; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "os_df":          pd.DataFrame(columns=OS_COLUMNS),
        "db_df":          pd.DataFrame(columns=DB_COLUMNS),
        "last_refresh":   None,
        "a1_status":      "idle",
        "a1_phase":       "idle",
        "a2_status":      "idle",
        "changes_log":    [],
        "old_os_df":      None,
        "old_db_df":      None,
        "a3_skip_until":  None,
        "os_row_count":   None,   # persists through rerun for debug banner
        "db_row_count":   None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()
refresh_agent  = RefreshAgent()
version_agent  = VersionGuardianAgent()
version_agent.init_session()
PolicyAnalysisAgent.init_session()


def badge(status: str) -> str:
    icons = {"idle":"◌","running":"⟳","done":"✓","error":"✕"}
    cls   = {"idle":"idle","running":"running","done":"done","error":"error"}.get(status,"idle")
    return f'<span class="badge b-{cls}">{icons.get(cls,"·")} {status.upper()}</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Infosys_logo.svg/1200px-Infosys_logo.svg.png",
                 width=130)
    except Exception:
        st.markdown("### INFY")
    st.divider()

    st.subheader("🔑 Anthropic API Key")
    api_key = st.text_input("Enter your API key", type="password",
                             placeholder="sk-ant-...",
                             help="Set ANTHROPIC_API_KEY in Streamlit Cloud Secrets to avoid typing each time.")
    if not api_key:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            pass

    key_ok = bool(api_key and api_key.startswith("sk-ant"))
    if api_key and not key_ok:
        st.error("⚠️ Key must start with sk-ant-")
    elif key_ok:
        st.success("✅ API key ready")

    st.divider()

    # Agent 1
    st.markdown(f"""<div class="agent-card a1">
    <b>🔍 Agent 1 — Live Data Fetcher</b><br>
    {badge(st.session_state.a1_status)}
    <small style="display:block;margin-top:4px;color:#666">
    Fetches ALL <b>OS &amp; DB</b> &amp; DB lifecycle data from the internet — no hardcoded baseline</small>
    </div>""", unsafe_allow_html=True)

    run_a1 = st.button("▶ Run Agent 1 — Fetch All Data", width="stretch",
                        disabled=not key_ok,
                        help="Searches 26 OS families + 34 DB products (60 total) via Claude AI web search")

    st.caption("⏱ Estimated time: 8–14 minutes (60 web searches)")
    st.divider()

    # Agent 2
    st.markdown(f"""<div class="agent-card a2">
    <b>🤖 Agent 2 — Recommendation Engine</b><br>
    {badge(st.session_state.a2_status)}
    <small style="display:block;margin-top:4px;color:#666">
    Generates expert AI recommendations for every fetched OS & DB row</small>
    </div>""", unsafe_allow_html=True)

    os_empty = st.session_state.os_df.empty
    db_empty = st.session_state.db_df.empty
    run_a2 = st.button("▶ Run Agent 2 — Generate Recommendations",
                        width="stretch",
                        disabled=not key_ok or (os_empty and db_empty),
                        help="Requires Agent 1 to have run first")

    if os_empty and db_empty:
        st.caption("⚠️ Run Agent 1 first to populate data")
    st.divider()

    # Agent 3
    st.markdown("""<div class="agent-card a3">
    <b>🔄 Agent 3 — Refresh Monitor</b>
    <small style="display:block;margin-top:4px;color:#666">
    Monitors 14-day schedule · seeks permission before re-running</small>
    </div>""", unsafe_allow_html=True)

    refresh_agent.render_status_card(
        st.session_state.last_refresh,
        os_count=len(st.session_state.os_df),
        db_count=len(st.session_state.db_df)
    )

    st.divider()

    # Agent 4
    st.markdown("""<div class="agent-card" style="border-color:#10B981;">
    <b>🛡️ Agent 4 — Version Guardian</b>
    <small style="display:block;margin-top:4px;color:#666">
    Snapshots data before every refresh · appends new data · never overwrites</small>
    </div>""", unsafe_allow_html=True)

    version_agent.render_status_card()

    st.divider()

    # Agent 5
    a5_status = st.session_state.get("a5_status", "idle")
    a5_icon   = {"idle":"⚪","interviewing":"🔵","principles":"🔵",
                 "costing":"🔵","ready_to_analyse":"🟡",
                 "analysing":"🔵","done":"✅"}.get(a5_status,"⚪")
    st.markdown(f"""<div class="agent-card" style="border-color:#7C3AED;">
    <b>{a5_icon} Agent 5 — Policy Analysis</b>
    <small style="display:block;margin-top:4px;color:#666">
    Policy interview → Guiding principles → Live cost data → Consolidated recommendations<br>
    Project: Apr 2026 → Jun 2028</small>
    </div>""", unsafe_allow_html=True)
    st.caption(f"Status: `{a5_status.upper()}`  |  Principles: {len(st.session_state.get('a5_principles',[]))}")

    st.divider()
    os_recs = (st.session_state.os_df["Recommendation"] != "").sum() if not os_empty else 0
    db_recs = (st.session_state.db_df["Recommendation"] != "").sum() if not db_empty else 0
    st.caption(f"📊 OS: **{len(st.session_state.os_df)}** rows · DB: **{len(st.session_state.db_df)}** rows")
    st.caption(f"💡 Recommendations: OS {os_recs} · DB {db_recs}")


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="infy-header">
  <h1>🖥️ INFY Migration Version Lifecycle Tracker</h1>
  <p>Infosys Enterprise Architecture &nbsp;·&nbsp;
     Live AI-Powered <strong>OS &amp; DB</strong> &amp; Database Lifecycle Intelligence &nbsp;·&nbsp;
     All data fetched dynamically from the internet &nbsp;·&nbsp;
     Powered by Claude AI (Anthropic)</p>
</div>
""", unsafe_allow_html=True)

# ── Persistent last-run row counts (survives st.rerun) ────────────────────────
_os_rc = st.session_state.get("os_row_count")
_db_rc = st.session_state.get("db_row_count")
if _os_rc is not None or _db_rc is not None:
    _os_display = f"**{_os_rc} OS versions**" if _os_rc else "**0 OS versions**"
    _db_display = f"**{_db_rc} DB versions**" if _db_rc else "**0 DB versions**"
    if (_os_rc or 0) + (_db_rc or 0) > 0:
        st.success(f"✅ Last Agent 1 run fetched {_os_display} and {_db_display}. "
                   f"Browse the tabs below.")
    else:
        st.error(
            "❌ **Agent 1 returned 0 rows.** The Anthropic API calls are failing. "
            "Check the progress bar messages above when you run Agent 1 — they now show "
            "the exact error (e.g. model not found, quota exceeded, network issue). "
            "Most common cause: API key quota exhausted. "
            "Check your usage at **console.anthropic.com**."
        )


# ── Agent 3 refresh banner ────────────────────────────────────────────────────
skip_until = st.session_state.get("a3_skip_until")
skip_active = skip_until and datetime.now() < skip_until

if (refresh_agent.is_refresh_due(st.session_state.last_refresh)
        and not skip_active and key_ok
        and not st.session_state.os_df.empty):
    approved = refresh_agent.render_refresh_banner(
        st.session_state.last_refresh,
        os_count=len(st.session_state.os_df),
        db_count=len(st.session_state.db_df)
    )
    if approved:
        # Agent 4: snapshot current data BEFORE refresh overwrites it
        if not st.session_state.os_df.empty or not st.session_state.db_df.empty:
            snap_ver = version_agent.snapshot_before_refresh(
                st.session_state.os_df,
                st.session_state.db_df,
                st.session_state.get("changes_log", [])
            )
            st.toast(f"🛡️ Agent 4 saved snapshot v{snap_ver} before refresh.", icon="💾")
        st.session_state.a1_status = "idle"
        st.session_state.a2_status = "idle"
        st.toast("✅ Refresh approved — click 'Run Agent 1' in the sidebar to start.", icon="🔄")


# ── Run Agent 1 ────────────────────────────────────────────────────────────────
if run_a1:
    st.session_state.a1_status = "running"
    st.session_state.a1_phase  = "fetching_os"
    st.session_state.old_os_df = st.session_state.os_df.copy() if not st.session_state.os_df.empty else None
    st.session_state.old_db_df = st.session_state.db_df.copy() if not st.session_state.db_df.empty else None

    agent1 = OSDataAgent(api_key=api_key)

    st.info("🔍 **Agent 1** is now searching the internet for all OS and DB lifecycle data. "
            "This will run ~40 searches. Progress shown below.")

    os_prog   = st.progress(0, text="Starting OS data fetch...")
    os_status = st.empty()

    def a1_os_cb(pct, msg):
        os_prog.progress(min(pct, 1.0), text=msg)
        os_status.caption(msg)

    try:
        new_os = agent1.fetch_all_os_data(progress_callback=a1_os_cb)
        st.session_state.os_df      = new_os
        st.session_state.os_row_count = len(new_os)   # persist through rerun
        st.session_state.a1_phase   = "fetching_db"
        os_status.caption(f"✅ OS fetch complete — **{len(new_os)} versions** across all OS families")
    except Exception as e:
        st.error(f"❌ OS fetch error: {e}")
        st.session_state.a1_status = "error"
        st.session_state.a1_phase  = "error"

    # Only proceed to DB fetch if OS succeeded
    if st.session_state.a1_status != "error":
        db_prog   = st.progress(0, text="Starting DB data fetch...")
        db_status = st.empty()

        def a1_db_cb(pct, msg):
            db_prog.progress(min(pct, 1.0), text=msg)
            db_status.caption(msg)

        try:
            new_db = agent1.fetch_all_db_data(progress_callback=a1_db_cb)
            st.session_state.db_df      = new_db
            st.session_state.db_row_count = len(new_db)   # persist through rerun
            st.session_state.a1_phase   = "done"
            db_status.caption(f"✅ DB fetch complete — **{len(new_db)} versions** across all DB products")
        except Exception as e:
            st.error(f"❌ DB fetch error: {e}")
            st.session_state.a1_status = "error"
            st.session_state.a1_phase  = "error"

    # Change detection
    changes = []
    if st.session_state.old_os_df is not None:
        changes += agent1.detect_os_changes(st.session_state.old_os_df, st.session_state.os_df)
    if st.session_state.old_db_df is not None:
        changes += agent1.detect_db_changes(st.session_state.old_db_df, st.session_state.db_df)

    st.session_state.changes_log  = changes
    st.session_state.last_refresh = datetime.now()
    # Reset Agent 5 analysis flags — new data means previous policy analysis is stale
    st.session_state["a5_os_analysed"] = False
    st.session_state["a5_db_analysed"] = False

    if st.session_state.a1_status != "error":
        st.session_state.a1_status = "done"
        st.session_state.a1_phase  = "done"

        # Agent 4: merge new data with any existing data (append, never overwrite)
        if st.session_state.old_os_df is not None or st.session_state.old_db_df is not None:
            old_os = st.session_state.old_os_df if st.session_state.old_os_df is not None else pd.DataFrame(columns=OS_COLUMNS)
            old_db = st.session_state.old_db_df if st.session_state.old_db_df is not None else pd.DataFrame(columns=DB_COLUMNS)
            merged_os, merged_db = version_agent.append_new_data(
                old_os, st.session_state.os_df,
                old_db, st.session_state.db_df
            )
            st.session_state.os_df = merged_os
            st.session_state.db_df = merged_db

        # Agent 4: record this as the latest version in history
        new_ver = version_agent.record_new_version(
            st.session_state.os_df,
            st.session_state.db_df,
            changes
        )

        st.success(
            f"✅ **Agent 1 complete!** Fetched **{len(st.session_state.os_df)} OS entries** "
            f"and **{len(st.session_state.db_df)} DB entries** from the web.\n\n"
            f"🛡️ **Agent 4** recorded this as version **v{new_ver}** in history."
            + (f"\n\n📋 **{len(changes)} data changes detected** since last refresh." if changes else "")
        )

    st.rerun()


# ── Run Agent 2 ────────────────────────────────────────────────────────────────
if run_a2:
    st.session_state.a2_status = "running"
    agent2 = RecommendationAgent(api_key=api_key)

    os_prog   = st.progress(0, text="Agent 2: generating OS recommendations...")
    os_status = st.empty()

    def a2_os_cb(pct, msg):
        os_prog.progress(min(pct, 1.0), text=msg)
        os_status.caption(msg)

    try:
        new_os = agent2.generate_os_recommendations(st.session_state.os_df, progress_callback=a2_os_cb)
        st.session_state.os_df = new_os
    except Exception as e:
        st.error(f"❌ OS recommendation error: {e}")
        st.session_state.a2_status = "error"

    db_prog   = st.progress(0, text="Agent 2: generating DB recommendations...")
    db_status = st.empty()

    def a2_db_cb(pct, msg):
        db_prog.progress(min(pct, 1.0), text=msg)
        db_status.caption(msg)

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
        st.success(f"✅ **Agent 2 complete!** Generated recommendations for "
                   f"**{os_filled} OS entries** and **{db_filled} DB entries**.")

    st.rerun()


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_os, tab_db, tab_status, tab_history, tab_agent5 = st.tabs([
    "🖥️ OS Versions", "🗄️ DB Versions",
    "📋 Agent Status & Log", "🛡️ Version History",
    "🧠 Agent 5 — Policy Analysis"
])


# ────────────────── Tab 1: OS Versions ────────────────────────────────────────
with tab_os:
    os_df   = st.session_state.os_df
    a1_phase = st.session_state.get("a1_phase", "idle")

    if os_df.empty and a1_phase in ("fetching_os", "fetching_db", "running"):
        st.markdown("""
        <div class="empty-state">
          <h3>⏳ Agent 1 is fetching OS data...</h3>
          <p>OS lifecycle data is being searched and collected right now.<br>
          This tab will populate automatically once the OS fetch phase completes.<br>
          <em>Watch the progress bar above for live updates.</em></p>
        </div>""", unsafe_allow_html=True)
        st.spinner("Fetching OS data from the internet...")
    elif os_df.empty:
        st.markdown("""
        <div class="empty-state">
          <h3>No OS data yet</h3>
          <p>Run <strong>Agent 1</strong> from the sidebar to fetch all OS lifecycle data from the internet.<br>
          Covers <strong>Windows 11/10/8/7 Client</strong>, Windows Server 2003–2025, Windows Embedded/IoT,
          RHEL, Ubuntu, SLES, Debian, CentOS, Rocky Linux, AlmaLinux, Oracle Linux,
          openSUSE, Fedora, macOS, Solaris, AIX, IBM i/z/OS, HP-UX,
          FreeBSD, OpenVMS, Tru64, Android, iOS/iPadOS.</p>
        </div>""", unsafe_allow_html=True)
    else:
        # Metrics
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

        # Filters
        with st.expander("🔍 Filters", expanded=False):
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                families = ["All"] + sorted(set(
                    v.split()[0] for v in os_df["OS Version"].dropna() if v and not v.startswith("[")
                ))
                fam_f = st.selectbox("OS Family", families)
            with fc2:
                upg_f = st.selectbox("Upgrade", ["All", "Y", "N"])
            with fc3:
                repl_f = st.selectbox("Replace", ["All", "Y", "N"])
            with fc4:
                rec_f = st.selectbox("Has Recommendation", ["All", "Yes", "No"])

        view = os_df.copy()
        if fam_f  != "All": view = view[view["OS Version"].str.startswith(fam_f, na=False)]
        if upg_f  != "All": view = view[view.get("Upgrade",  pd.Series(dtype=str)) == upg_f]
        if repl_f != "All": view = view[view.get("Replace",  pd.Series(dtype=str)) == repl_f]
        if rec_f  == "Yes": view = view[view["Recommendation"] != ""]
        if rec_f  == "No":  view = view[view["Recommendation"] == ""]

        st.caption(f"Showing {len(view)} of {len(os_df)} OS entries")

        st.dataframe(
            view, width="stretch", height=520, hide_index=True,
            column_config={
                "OS Version":                    st.column_config.TextColumn("OS Version",        width=220),
                "Availability Date":             st.column_config.TextColumn("Available",         width=110),
                "Security/Standard Support End": st.column_config.TextColumn("Security End",      width=120),
                "Mainstream/Full Support End":   st.column_config.TextColumn("Mainstream End",    width=140),
                "Extended/LTSC Support End":     st.column_config.TextColumn("Extended End",      width=120),
                "Notes":                         st.column_config.TextColumn("Notes",             width=160),
                "Recommendation":                st.column_config.TextColumn("💡 Recommendation", width=420),
                "Upgrade":                       st.column_config.TextColumn("⬆ Upgrade",         width=80),
                "Replace":                       st.column_config.TextColumn("🔁 Replace",        width=80),
                "Primary Alternative":           st.column_config.TextColumn("Primary Alt",       width=160),
                "Secondary Alternative":         st.column_config.TextColumn("Secondary Alt",     width=140),
            }
        )


# ────────────────── Tab 2: DB Versions ────────────────────────────────────────
with tab_db:
    db_df    = st.session_state.db_df
    a1_phase = st.session_state.get("a1_phase", "idle")

    if db_df.empty and a1_phase == "fetching_db":
        # DB fetch is actively running right now
        st.markdown("""
        <div class="empty-state" style="border-color:#F59E0B;">
          <h3>⏳ Agent 1 is fetching DB data now...</h3>
          <p>OS data fetch is complete. Database lifecycle data is now being collected.<br>
          Searching SQL Server · Oracle · PostgreSQL · MySQL · MariaDB · MongoDB · Redis ·
          Cassandra · Elasticsearch · SAP HANA · Teradata · Aurora · RDS · Neo4j · InfluxDB ·
          Snowflake · Databricks · Azure SQL · Cosmos DB and more.<br><br>
          <strong>This tab will populate as soon as all 20 DB searches complete.</strong></p>
        </div>""", unsafe_allow_html=True)
        st.info("🔍 DB fetch in progress — check the progress bar above for live status.")

    elif db_df.empty and a1_phase == "fetching_os":
        # Still on OS phase, DB hasn't started yet
        st.markdown("""
        <div class="empty-state" style="border-color:#0EA5E9;">
          <h3>⏳ Agent 1 is fetching OS data first...</h3>
          <p>OS lifecycle data is being collected. DB fetch will start automatically once OS is done.<br>
          <em>Please wait — DB data will appear here shortly.</em></p>
        </div>""", unsafe_allow_html=True)

    elif db_df.empty and a1_phase in ("running",):
        st.markdown("""
        <div class="empty-state" style="border-color:#0EA5E9;">
          <h3>⏳ Agent 1 is running...</h3>
          <p>DB data will appear here once Agent 1 completes the database fetch phase.</p>
        </div>""", unsafe_allow_html=True)

    elif db_df.empty:
        st.markdown("""
        <div class="empty-state">
          <h3>No DB data yet</h3>
          <p>Run <strong>Agent 1</strong> to fetch all database lifecycle data from the internet.<br>
          Covers SQL Server, Oracle, PostgreSQL, MySQL, MariaDB, MongoDB, Redis, Cassandra,
          Elasticsearch, SAP HANA, Teradata, Aurora, RDS, Neo4j, InfluxDB, Snowflake and more.</p>
        </div>""", unsafe_allow_html=True)
    else:
        # Metrics
        dm1, dm2, dm3, dm4, dm5 = st.columns(5)
        eol_db  = (db_df.get("Status", pd.Series(dtype=str)).str.lower() == "end of life").sum()
        exp_db  = (db_df.get("Status", pd.Series(dtype=str)).str.lower() == "expiring soon").sum()
        sup_db  = (db_df.get("Status", pd.Series(dtype=str)).str.lower() == "supported").sum()
        rec_db  = (db_df["Recommendation"] != "").sum()

        with dm1: st.metric("Total DB Entries",  len(db_df))
        with dm2: st.metric("🔴 End of Life",    int(eol_db))
        with dm3: st.metric("🟡 Expiring Soon",  int(exp_db))
        with dm4: st.metric("🟢 Supported",      int(sup_db))
        with dm5: st.metric("💡 Recommendations",int(rec_db))

        # Filters
        with st.expander("🔍 Filters", expanded=False):
            df1, df2, df3, df4 = st.columns(4)
            with df1:
                dbs = ["All"] + sorted(db_df["Database"].dropna().unique().tolist())
                db_f = st.selectbox("Database", dbs)
            with df2:
                types = ["All"] + sorted(db_df["Type"].dropna().unique().tolist())
                type_f = st.selectbox("Type", types)
            with df3:
                statuses = ["All"] + sorted(db_df["Status"].dropna().unique().tolist())
                stat_f = st.selectbox("Status", statuses)
            with df4:
                repl_db_f = st.selectbox("Replace Flag", ["All", "Y", "N"], key="repl_db")

        view_db = db_df.copy()
        if db_f    != "All": view_db = view_db[view_db["Database"] == db_f]
        if type_f  != "All": view_db = view_db[view_db["Type"]     == type_f]
        if stat_f  != "All": view_db = view_db[view_db["Status"]   == stat_f]
        if repl_db_f != "All": view_db = view_db[view_db.get("Replace", pd.Series(dtype=str)) == repl_db_f]

        def _style_status(val):
            m = {"end of life":"background-color:#FFCDD2;color:#B71C1C",
                 "expiring soon":"background-color:#FFE0B2;color:#E65100",
                 "supported":"background-color:#C8E6C9;color:#1B5E20",
                 "future":"background-color:#E3F2FD;color:#0D47A1"}
            return m.get(str(val).lower(), "")

        st.caption(f"Showing {len(view_db)} of {len(db_df)} DB entries")

        st.dataframe(
            view_db.style.map(_style_status, subset=["Status"]) if "Status" in view_db.columns else view_db,
            width="stretch", height=520, hide_index=True,
            column_config={
                "Database":               st.column_config.TextColumn("Database",        width=130),
                "Version":                st.column_config.TextColumn("Version",         width=100),
                "Type":                   st.column_config.TextColumn("Type",            width=150),
                "Mainstream / Premier End":st.column_config.TextColumn("Mainstream End", width=130),
                "Extended Support End":   st.column_config.TextColumn("Extended End",    width=120),
                "Status":                 st.column_config.TextColumn("Status",          width=120),
                "Notes":                  st.column_config.TextColumn("Notes",           width=180),
                "Recommendation":         st.column_config.TextColumn("💡 Recommendation",width=420),
                "Upgrade":                st.column_config.TextColumn("⬆ Upgrade",       width=80),
                "Replace":                st.column_config.TextColumn("🔁 Replace",      width=80),
                "Primary Alternative":    st.column_config.TextColumn("Primary Alt",     width=150),
                "Secondary Alternative":  st.column_config.TextColumn("Secondary Alt",   width=140),
            }
        )


with tab_history:
    st.subheader("🛡️ Version History — Agent 4")
    st.caption(
        "Every time Agent 3 approves a refresh, Agent 4 snapshots the current data "
        "before Agent 1 runs. New data is then **appended** rather than overwriting. "
        "All versions are available here and included in the Excel download."
    )
    st.divider()
    version_agent.render_history_viewer()


# ── Tab 3: Agent Status ───────────────────────────────────────────────────────
with tab_status:
    st.subheader("🤖 Agent Activity Dashboard")

    ca1, ca2, ca3 = st.columns(3)

    s1 = st.session_state.a1_status
    with ca1:
        icon1 = {"idle":"⚪","running":"🔵","done":"✅","error":"❌"}.get(s1,"⚪")
        st.markdown(f"""**{icon1} Agent 1 — Live Data Fetcher**
- Status: `{s1.upper()}`
- Fetches ALL OS & DB lifecycle data from the web — no hardcoded data
- Tool: Claude AI + web\\_search · **60 searches total**
- **OS families (26):** Windows 11/10/8/7/Vista/XP, Windows Server 2003–2025, Windows Embedded/IoT, RHEL 4–10, Ubuntu 12.04–25.04, SLES 10–16, Debian 6–13, CentOS/Stream, Rocky/AlmaLinux, Oracle Linux, openSUSE/Fedora, Arch/Gentoo, macOS, Solaris, AIX, IBM i/z/OS, HP-UX, FreeBSD, OpenVMS/Tru64, Android, iOS/iPadOS
- **DB products (34):** SQL Server, Oracle DB, PostgreSQL, MySQL, MariaDB, IBM Db2, IBM Informix, IBM IMS/Netezza, Sybase ASE, SAP HANA, SAP IQ, MongoDB, Redis, Cassandra, Elasticsearch/OpenSearch, Teradata, Vertica/Greenplum, Ingres/Actian, Progress/Firebird, InterBase, SQLite/H2, MS Access/FoxPro, Aurora/RDS, DynamoDB/DocumentDB, Google Spanner/BigQuery, Azure SQL/Cosmos DB, CockroachDB/YugabyteDB, CouchDB/Couchbase, Neo4j, InfluxDB/TimescaleDB, Snowflake/Databricks, Hive/HBase, Exasol/SingleStore, SAP MaxDB""")

    s2 = st.session_state.a2_status
    with ca2:
        icon2 = {"idle":"⚪","running":"🔵","done":"✅","error":"❌"}.get(s2,"⚪")
        st.markdown(f"""**{icon2} Agent 2 — Recommendation Engine**
- Status: `{s2.upper()}`
- Generates expert recommendations per row
- Tool: Claude claude-sonnet-4-6
- Batch size: 20 rows per API call
- Rules: EOL → CRITICAL, Expiring → URGENT, Supported → PLAN
- Oracle versions: flags PostgreSQL migration opportunity""")

    with ca3:
        last_r    = st.session_state.last_refresh
        days_left = refresh_agent.days_until_refresh(last_r)
        due       = refresh_agent.is_refresh_due(last_r)
        icon3     = "🟡" if due else ("✅" if last_r else "⚪")
        last_str  = last_r.strftime("%d %b %Y %H:%M") if last_r else "Never"
        st.markdown(f"""**{icon3} Agent 3 — Refresh Monitor**
- Status: `{"REFRESH DUE" if due else ("MONITORING" if last_r else "WAITING")}`
- Interval: Every 14 days
- Last refresh: {last_str}
- Next refresh: {f"In {days_left} days" if last_r else "After first Agent 1 run"}
- Behaviour: Shows permission banner → user approves → re-runs Agents 1 & 2""")

    # Agent 4
    ca4, _, _ = st.columns(3)
    vcount = version_agent.get_version_count()
    latest = version_agent.get_latest()
    icon4  = "✅" if vcount > 0 else "⚪"
    with ca4:
        st.markdown(f"""**{icon4} Agent 4 — Version Guardian**
- Status: `{"ACTIVE — {vcount} VERSION(S) STORED" if vcount else "WAITING"}`
- Behaviour: Snapshots data BEFORE every approved refresh
- Merge strategy: New data appended, no rows ever deleted
- Excel: One OS + DB + Changes sheet per version
- Latest: {latest["label"] if latest else "None yet"}
- Max versions in session: 10""")

    # Changes log
    if st.session_state.changes_log:
        st.divider()
        st.subheader(f"📋 Change Log — Last Agent 1 Run ({len(st.session_state.changes_log)} changes)")
        for c in st.session_state.changes_log:
            st.markdown(f"- {c}")
    else:
        st.info("No change log yet. Agent 3 will populate this after the second Agent 1 run, "
                "comparing old vs new lifecycle data.")

    st.divider()
    st.subheader("📖 How to Use")
    st.markdown("""
1. **Enter your Anthropic API key** in the sidebar (or add `ANTHROPIC_API_KEY` to Streamlit Cloud Secrets)
2. **Run Agent 1** — fetches ALL OS & DB lifecycle data live from the internet (38 searches, ~3–6 min)
3. **Run Agent 2** — Claude AI generates expert migration recommendations for every row
4. **Browse & filter** the OS Versions and DB Versions tabs
5. **Download Excel** below — formatted `.xlsx` with both sheets, colour-coded, recommendations included
6. **Agent 3** automatically prompts you every 14 days to re-run and pick up any lifecycle changes

**Streamlit Cloud deployment:**
- Push this folder to GitHub
- Deploy at [share.streamlit.io](https://share.streamlit.io)
- In App Settings → Secrets add: `ANTHROPIC_API_KEY = "sk-ant-..."`
    """)


with tab_agent5:
    # Recreate agent with live api_key
    live_agent5 = PolicyAnalysisAgent(api_key=api_key) if key_ok else PolicyAnalysisAgent(api_key="dummy")
    render_agent5_tab(live_agent5, key_ok)


# ── Download Excel ─────────────────────────────────────────────────────────────
st.divider()
_, dl_col, _ = st.columns([1, 2, 1])

with dl_col:
    ts_str = datetime.now().strftime("%d %b %Y %H:%M UTC")
    excel_bytes = export_to_excel(
        st.session_state.os_df,
        st.session_state.db_df,
        generated_at=ts_str,
        version_history=version_agent.get_history(),
        principles=st.session_state.get("a5_principles", []),
        costs=st.session_state.get("a5_costs", {})
    )
    fname = f"INFY_Version_Tracker_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    os_n  = len(st.session_state.os_df)
    db_n  = len(st.session_state.db_df)
    label = (
        f"📥 Download Excel  —  OS: {os_n} entries · DB: {db_n} entries"
        if (os_n or db_n) else
        "📥 Download Excel  (run Agent 1 first to populate data)"
    )

    st.download_button(
        label=label,
        data=excel_bytes,
        file_name=fname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
        type="primary",
        help="Downloads OS Versions + DB Versions + Summary in one formatted Excel workbook"
    )
    st.caption(f"📁 {fname}  ·  Generated at {ts_str}")

st.markdown(
    "<p style='text-align:center;color:#94A3B8;font-size:0.72rem;margin-top:1.5rem;'>"
    "INFY Migration Reference Tracker · Infosys Enterprise Architecture · "
    "Powered by Claude AI (Anthropic) · claude-sonnet-4-6 · All data fetched live from the internet</p>",
    unsafe_allow_html=True
)
