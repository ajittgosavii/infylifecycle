"""
INFY Migration Version Lifecycle Tracker
5-Agent Streamlit Application — Infosys Enterprise Architecture

Core design:
- baseline_data.py holds ALL 321 OS/DB rows from AI training knowledge
- Data is visible IMMEDIATELY on app load — no waiting for Agent 1
- Agent 1 checks internet for date changes and updates Notes column
- Agent 2 fills Recommendation column via OpenAI
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
_m_store     = _load("utils.data_store",       "utils/data_store.py")
_m_risk      = _load("utils.risk_scoring",     "utils/risk_scoring.py")
_m_dashboard = _load("utils.dashboard",        "utils/dashboard.py")
_m_config    = _load("utils.config",           "utils/config.py")
_m_inventory = _load("utils.inventory_upload",  "utils/inventory_upload.py")
_m_scenario  = _load("utils.scenario_planner",  "utils/scenario_planner.py")
_m_pdf       = _load("utils.pdf_report",        "utils/pdf_report.py")

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
WS_DATA              = _m_baseline.WS_DATA
WS_COLUMNS           = _m_baseline.WS_COLUMNS
AS_DATA              = _m_baseline.AS_DATA
AS_COLUMNS           = _m_baseline.AS_COLUMNS
FW_DATA              = _m_baseline.FW_DATA
FW_COLUMNS           = _m_baseline.FW_COLUMNS

# Data store helpers
save_os_df      = _m_store.save_os_df
save_db_df      = _m_store.save_db_df
load_os_df      = _m_store.load_os_df
load_db_df      = _m_store.load_db_df
save_app_state  = _m_store.save_app_state
load_app_state  = _m_store.load_app_state
has_stored_data = _m_store.has_stored_data
get_rec_stats   = _m_store.get_rec_stats

# New enhancement modules
add_risk_scores       = _m_risk.add_risk_scores
get_risk_summary      = _m_risk.get_risk_summary
risk_distribution_chart = _m_dashboard.risk_distribution_chart
status_breakdown_chart  = _m_dashboard.status_breakdown_chart
eol_timeline_chart      = _m_dashboard.eol_timeline_chart
top_urgent_items        = _m_dashboard.top_urgent_items
risk_score_histogram    = _m_dashboard.risk_score_histogram
render_project_settings = _m_config.render_project_settings
get_project_end         = _m_config.get_project_end
render_upload_section   = _m_inventory.render_upload_section
match_os_inventory      = _m_inventory.match_os_inventory
match_db_inventory      = _m_inventory.match_db_inventory
render_inventory_results = _m_inventory.render_inventory_results
render_scenario_planner  = _m_scenario.render_scenario_planner
generate_pdf_report      = _m_pdf.generate_pdf_report

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="INFY Version Lifecycle Tracker",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "INFY Migration Version Lifecycle Tracker — Powered by OpenAI GPT"}
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
.stTabs [data-baseweb="tab-list"] {
    justify-content: center;
}
.b-error   { background:#FEE2E2; color:#991B1B; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    if "os_df" not in st.session_state:
        # ── Load from SQLite if data exists, else load baseline and save it ──
        if has_stored_data():
            stored_os = load_os_df()
            stored_db = load_db_df()
            st.session_state["os_df"] = stored_os
            st.session_state["db_df"] = stored_db
        else:
            # First ever run — load baseline and immediately persist to SQLite
            baseline_os = pd.DataFrame(OS_DATA)
            baseline_db = pd.DataFrame(DB_DATA)
            save_os_df(baseline_os)
            save_db_df(baseline_db)
            st.session_state["os_df"] = baseline_os
            st.session_state["db_df"] = baseline_db

    # ── Web Servers, App Servers, Frameworks — always from baseline ──
    if "ws_df" not in st.session_state:
        st.session_state["ws_df"] = pd.DataFrame(WS_DATA)
    if "as_df" not in st.session_state:
        st.session_state["as_df"] = pd.DataFrame(AS_DATA)
    if "fw_df" not in st.session_state:
        st.session_state["fw_df"] = pd.DataFrame(FW_DATA)

    # Restore last_refresh from SQLite so Agent 3 timer survives restarts
    if "last_refresh" not in st.session_state:
        saved_refresh = load_app_state("last_refresh")
        if saved_refresh:
            try:
                st.session_state["last_refresh"] = datetime.fromisoformat(saved_refresh)
            except Exception:
                st.session_state["last_refresh"] = None
        else:
            st.session_state["last_refresh"] = None

    # Other session defaults
    for k, v in {
        "a1_status": "idle", "a2_status": "idle",
        "changes_log": [], "old_os_df": None, "old_db_df": None,
        "a3_skip_until": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()
refresh_agent = RefreshAgent()
VersionGuardianAgent.init_session()
PolicyAnalysisAgent.init_session()

# ── Compute risk scores on every load ─────────────────────────────────────
if "Risk Score" not in st.session_state.os_df.columns:
    st.session_state.os_df = add_risk_scores(st.session_state.os_df, "OS")
if "Risk Score" not in st.session_state.db_df.columns:
    st.session_state.db_df = add_risk_scores(st.session_state.db_df, "DB")
if "Risk Score" not in st.session_state.ws_df.columns:
    st.session_state.ws_df = add_risk_scores(st.session_state.ws_df, "DB")
if "Risk Score" not in st.session_state.as_df.columns:
    st.session_state.as_df = add_risk_scores(st.session_state.as_df, "DB")
if "Risk Score" not in st.session_state.fw_df.columns:
    st.session_state.fw_df = add_risk_scores(st.session_state.fw_df, "DB")


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

    st.subheader("🔑 OpenAI API Key")
    api_key = st.text_input("Enter your API key", type="password", placeholder="sk-...",
                             help="Set OPENAI_API_KEY in Streamlit Cloud Secrets.")
    if not api_key:
        try: api_key = st.secrets["OPENAI_API_KEY"]
        except Exception: pass

    key_ok = bool(api_key and api_key.startswith("sk-"))
    if api_key and not key_ok: st.error("⚠️ Key must start with sk-")
    elif key_ok: st.success("✅ API key ready")
    st.divider()

    # Agent 1 — Sentinel
    s1 = st.session_state.a1_status
    st.markdown(f"""<div class="agent-card a1">
    <b>🔍 Sentinel — Lifecycle Scanner</b><br>{badge(s1)}
    <small style="display:block;margin-top:4px;color:#666">
    Scans the web for lifecycle date changes.<br>
    Pre-loaded: {len(OS_DATA)} OS + {len(DB_DATA)} DB = {len(OS_DATA)+len(DB_DATA)} entries</small>
    </div>""", unsafe_allow_html=True)
    run_a1 = st.button("▶ Run Sentinel — Scan for Updates", width="stretch", disabled=not key_ok)
    st.caption("⏱ ~2–3 min (16 targeted web checks)")
    st.divider()

    # Agent 2 — Advisor
    s2 = st.session_state.a2_status
    st.markdown(f"""<div class="agent-card a2">
    <b>🤖 Advisor — AI Recommendation Engine</b><br>{badge(s2)}
    <small style="display:block;margin-top:4px;color:#666">
    Generates expert migration recommendations for all rows</small>
    </div>""", unsafe_allow_html=True)
    run_a2 = st.button("▶ Run Advisor — Generate Recommendations", width="stretch", disabled=not key_ok)
    st.divider()

    # Agent 3 — Watchdog
    st.markdown("""<div class="agent-card a3">
    <b>🔄 Watchdog — Refresh Monitor</b>
    <small style="display:block;margin-top:4px;color:#666">
    14-day schedule · seeks permission before re-running</small>
    </div>""", unsafe_allow_html=True)
    refresh_agent.render_status_card(
        st.session_state.last_refresh,
        os_count=len(st.session_state.os_df),
        db_count=len(st.session_state.db_df),
        ws_count=len(st.session_state.ws_df),
        as_count=len(st.session_state.as_df),
        fw_count=len(st.session_state.fw_df)
    )
    st.divider()

    st.divider()

    # Agent 4 / 5
    history = VersionGuardianAgent.get_history()
    a5s = st.session_state.get("a5_status", "idle")
    st.markdown(f"""<div class="agent-card a4">
    <b>🛡️ Guardian — Version Snapshot Manager</b>
    <small style="display:block;margin-top:4px;color:#666">{len(history)} snapshot(s)</small></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="agent-card a5">
    <b>🧠 Strategist — Policy Analysis Engine</b><br>{badge(a5s)}
    <small style="display:block;margin-top:4px;color:#666">Apr 2026 → Jun 2028</small>
    </div>""", unsafe_allow_html=True)
    _a5_open = st.session_state.get("show_strategist", False)
    _a5_label = "✕ Close Strategist" if _a5_open else "▶ Open Strategist"
    if st.button(_a5_label, width="stretch", key="open_a5"):
        st.session_state["show_strategist"] = not _a5_open
        st.rerun()
    st.divider()

    os_recs = (st.session_state.os_df["Recommendation"] != "").sum()
    db_recs = (st.session_state.db_df["Recommendation"] != "").sum()
    st.caption(f"📊 OS: **{len(st.session_state.os_df)}** · DB: **{len(st.session_state.db_df)}** · WS: **{len(st.session_state.ws_df)}** · AS: **{len(st.session_state.as_df)}** · FW: **{len(st.session_state.fw_df)}** rows")
    st.caption(f"💡 Recommendations: OS {os_recs} · DB {db_recs}")

    # ── Persistence status ────────────────────────────────────────────────────
    st.divider()
    stats = get_rec_stats()
    last_saved = stats.get("last_saved", "Never")
    if last_saved and last_saved != "Never":
        try:
            last_saved = datetime.fromisoformat(last_saved).strftime("%d %b %Y %H:%M")
        except Exception:
            pass
    if stats["os_with_recs"] > 0 or stats["db_with_recs"] > 0:
        st.markdown(
            f"<div style='background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;"
            f"padding:0.5rem 0.75rem;font-size:0.78rem;color:#166534;'>"
            f"💾 <strong>Database</strong><br>"
            f"OS: {stats['os_with_recs']}/{stats['os_total']} recs stored<br>"
            f"DB: {stats['db_with_recs']}/{stats['db_total']} recs stored<br>"
            f"Last saved: {last_saved}"
            f"</div>", unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div style='background:#FFF7ED;border:1px solid #FED7AA;border-radius:8px;"
            f"padding:0.5rem 0.75rem;font-size:0.78rem;color:#92400E;'>"
            f"💾 <strong>Database</strong><br>"
            f"No recommendations stored yet.<br>"
            f"Run Agent 2 to generate &amp; persist."
            f"</div>", unsafe_allow_html=True
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TOOLS SECTION — Inventory Upload, What-If Planner, Agent Status, History
    # ══════════════════════════════════════════════════════════════════════════
    st.divider()
    st.markdown("""<div style='background:linear-gradient(135deg,#0F172A,#1E293B);
        padding:0.6rem 0.8rem;border-radius:8px;margin-bottom:0.6rem;'>
        <span style='color:#F59E0B;font-weight:700;font-size:0.85rem;'>🧰 TOOLS & UTILITIES</span>
    </div>""", unsafe_allow_html=True)

    # ── Inventory Upload (sidebar) ───────────────────────────────────────────
    with st.expander("📤 Inventory Upload", expanded=False):
        matched_os_inv, matched_db_inv = render_upload_section()
        if matched_os_inv is not None:
            with st.spinner("Matching OS inventory..."):
                enriched_os = match_os_inventory(matched_os_inv, st.session_state.os_df)
                st.session_state["inv_matched_os"] = enriched_os
        if matched_db_inv is not None:
            with st.spinner("Matching DB inventory..."):
                enriched_db = match_db_inventory(matched_db_inv, st.session_state.db_df)
                st.session_state["inv_matched_db"] = enriched_db
        stored_os_inv = st.session_state.get("inv_matched_os")
        stored_db_inv = st.session_state.get("inv_matched_db")
        if stored_os_inv is not None or stored_db_inv is not None:
            render_inventory_results(stored_os_inv, stored_db_inv)

    # ── What-If Planner (sidebar) ────────────────────────────────────────────
    with st.expander("🔮 What-If Planner", expanded=False):
        render_scenario_planner(st.session_state.os_df, st.session_state.db_df)

    # ── Agent Status & Log (sidebar) ─────────────────────────────────────────
    with st.expander("📋 Agent Status & Log", expanded=False):
        s1 = st.session_state.a1_status
        s2 = st.session_state.a2_status
        icon1 = {"idle":"⚪","running":"🔵","done":"✅","error":"❌"}.get(s1,"⚪")
        icon2 = {"idle":"⚪","running":"🔵","done":"✅","error":"❌"}.get(s2,"⚪")
        st.markdown(f"{icon1} **Sentinel**: `{s1.upper()}`")
        st.markdown(f"{icon2} **Advisor**: `{s2.upper()}`")
        last_r = st.session_state.last_refresh
        days_left = refresh_agent.days_until_refresh(last_r)
        due = refresh_agent.is_refresh_due(last_r)
        icon3 = "🟡" if due else ("✅" if last_r else "⚪")
        last_str = last_r.strftime("%d %b %H:%M") if last_r else "Never"
        st.markdown(f"{icon3} **Watchdog**: `{'DUE' if due else ('OK' if last_r else 'WAIT')}`  \nLast: {last_str}")
        h = VersionGuardianAgent.get_history()
        st.markdown(f"🛡️ **Guardian**: {len(h)} snapshot(s)")
        a5s_sb = st.session_state.get("a5_status","idle")
        gps_sb = st.session_state.get("a5_principles",[])
        st.markdown(f"🧠 **Strategist**: `{a5s_sb.upper()}` · {len(gps_sb)} principles")
        if st.session_state.changes_log:
            st.caption(f"📋 {len(st.session_state.changes_log)} changes from last Agent 1 run")
            for c in st.session_state.changes_log[:5]:
                st.markdown(f"<small>- {c}</small>", unsafe_allow_html=True)
            if len(st.session_state.changes_log) > 5:
                st.caption(f"... and {len(st.session_state.changes_log)-5} more")

    # ── Version History (sidebar) ────────────────────────────────────────────
    with st.expander("🛡️ Version History", expanded=False):
        VersionGuardianAgent.render_history_tab()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="infy-header">
  <h1>🖥️ INFY Migration Version Lifecycle Tracker</h1>
  <p>Infosys Enterprise Architecture &nbsp;·&nbsp;
     Powered by OpenAI GPT &nbsp;·&nbsp;
     {len(OS_DATA)} OS + {len(DB_DATA)} DB + {len(WS_DATA)} Web Servers + {len(AS_DATA)} App Servers + {len(FW_DATA)} Frameworks &nbsp;·&nbsp;
     Risk Dashboard · Scenario Planner · Inventory Upload · PDF Reports &nbsp;·&nbsp;
     5 AI Agents: Sentinel · Advisor · Watchdog · Guardian · Strategist</p>
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
        db_count=len(st.session_state.db_df),
        ws_count=len(st.session_state.ws_df),
        as_count=len(st.session_state.as_df),
        fw_count=len(st.session_state.fw_df)
    )
    if approved:
        VersionGuardianAgent.snapshot(
            st.session_state.os_df,
            st.session_state.db_df,
            st.session_state.changes_log,
            ws_df=st.session_state.ws_df,
            as_df=st.session_state.as_df,
            fw_df=st.session_state.fw_df
        )
        st.session_state.a1_status = "idle"
        st.session_state.a2_status = "idle"
        st.session_state.a5_os_done = False
        st.session_state.a5_db_done = False
        st.session_state.a5_ws_done = False
        st.session_state.a5_as_done = False
        st.session_state.a5_fw_done = False
        st.toast("✅ Refresh approved — click 'Run Agent 1' to check for updates.", icon="🔄")


# ── Run Agent 1 ────────────────────────────────────────────────────────────────
if run_a1:
    st.session_state.a1_status = "running"
    if not st.session_state.os_df.empty:
        VersionGuardianAgent.snapshot(
            st.session_state.os_df,
            st.session_state.db_df,
            st.session_state.changes_log,
            ws_df=st.session_state.ws_df,
            as_df=st.session_state.as_df,
            fw_df=st.session_state.fw_df
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
        new_os, new_db, new_ws, new_as, new_fw, changes = agent1.merge_updates_into_df(
            st.session_state.os_df,
            st.session_state.db_df,
            updates,
            ws_df=st.session_state.ws_df,
            as_df=st.session_state.as_df,
            fw_df=st.session_state.fw_df
        )
        # Recompute risk scores after update
        new_os = add_risk_scores(new_os, "OS")
        new_db = add_risk_scores(new_db, "DB")
        new_ws = add_risk_scores(new_ws, "DB")
        new_as = add_risk_scores(new_as, "DB")
        new_fw = add_risk_scores(new_fw, "DB")
        st.session_state.os_df     = new_os
        st.session_state.db_df     = new_db
        st.session_state.ws_df     = new_ws
        st.session_state.as_df     = new_as
        st.session_state.fw_df     = new_fw
        st.session_state.changes_log = changes
        st.session_state.last_refresh = datetime.now()
        st.session_state.a1_status    = "done"
        st.session_state.a5_os_done   = False
        st.session_state.a5_db_done   = False
        st.session_state.a5_ws_done   = False
        st.session_state.a5_as_done   = False
        st.session_state.a5_fw_done   = False

        # ── Persist Agent 1 date changes to SQLite ────────────────────────────
        save_os_df(new_os)
        save_db_df(new_db)
        save_app_state("last_refresh", datetime.now().isoformat())

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

    # ── Checkpoint 1: Pre-flight ──────────────────────────────────────────────
    st.markdown("### 🤖 Agent 2 — Recommendation Engine")
    chk1 = st.empty()
    chk1.info("🔌 **Checkpoint 1/4** — Testing OpenAI gpt-4o-mini API connection...")

    try:
        from openai import OpenAI as _OAI2
        _c2 = _OAI2(api_key=api_key)
        _model2 = None
        for _m2 in ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-3.5-turbo-0125"]:
            try:
                _r2 = _c2.chat.completions.create(
                    model=_m2, max_tokens=20,
                    messages=[{"role": "user", "content": "Reply: READY"}]
                )
                _model2 = _m2
                st.session_state["_openai_model"] = _m2
                break
            except Exception as _me2:
                if "not found" in str(_me2).lower() or "404" in str(_me2):
                    continue
                raise _me2
        if not _model2:
            raise Exception("No supported model found on this OpenAI account")
        _reply2 = _r2.choices[0].message.content.strip()
        chk1.success(f"✅ **Checkpoint 1/4 PASSED** — OpenAI `{_model2}` connected. Response: **{_reply2}**")
    except Exception as _ex2:
        chk1.error(
            f"❌ **Checkpoint 1/4 FAILED** — OpenAI API not reachable.\n\n"
            f"**Error:** `{str(_ex2)}`\n\n"
            f"Check API key and quota at platform.openai.com/usage"
        )
        st.session_state.a2_status = "error"
        st.stop()

    # ── Checkpoint 2: OS Recommendations ─────────────────────────────────────
    agent2 = RecommendationAgent(api_key=api_key)   # ← instantiate here
    chk2 = st.empty()
    chk2.info(f"🧠 **Checkpoint 2/4** — OpenAI generating OS recommendations "
              f"({len(st.session_state.os_df)} rows, batches of 20)...")
    os_prog = st.progress(0, text="Processing OS rows...")
    os_live = st.empty()

    def a2_os_cb(pct, msg):
        os_prog.progress(min(pct, 1.0), text=msg)
        os_live.caption(f"↳ {msg}")

    try:
        new_os = agent2.generate_os_recommendations(
            st.session_state.os_df, progress_callback=a2_os_cb)
        st.session_state.os_df = new_os
        os_filled = (new_os["Recommendation"] != "").sum()
        # ── Save OS recommendations to SQLite immediately ─────────────────────
        save_os_df(new_os)
        chk2.success(f"✅ **Checkpoint 2/4 PASSED** — OS recommendations filled: "
                     f"**{os_filled} / {len(new_os)} rows** · 💾 Saved to database")
    except Exception as e:
        chk2.error(f"❌ **Checkpoint 2/4 FAILED** — OS recommendations error: `{e}`")
        st.session_state.a2_status = "error"
        st.stop()
    chk3 = st.empty()
    chk3.info(f"🧠 **Checkpoint 3/4** — OpenAI generating DB recommendations "
              f"({len(st.session_state.db_df)} rows, batches of 20)...")
    db_prog = st.progress(0, text="Processing DB rows...")
    db_live = st.empty()

    def a2_db_cb(pct, msg):
        db_prog.progress(min(pct, 1.0), text=msg)
        db_live.caption(f"↳ {msg}")

    try:
        new_db = agent2.generate_db_recommendations(
            st.session_state.db_df, progress_callback=a2_db_cb)
        st.session_state.db_df = new_db
        db_filled = (new_db["Recommendation"] != "").sum()
        # ── Save DB recommendations to SQLite immediately ─────────────────────
        save_db_df(new_db)
        chk3.success(f"✅ **Checkpoint 3/4 PASSED** — DB recommendations filled: "
                     f"**{db_filled} / {len(new_db)} rows** · 💾 Saved to database")
    except Exception as e:
        chk3.error(f"❌ **Checkpoint 3/4 FAILED** — DB recommendations error: `{e}`")
        st.session_state.a2_status = "error"
        st.stop()

    # ── Checkpoint 3.5: WS / AS / FW Recommendations ─────────────────────────
    chk35 = st.empty()
    chk35.info("🧠 **Checkpoint 3.5/4** — Generating Web Server, App Server & Framework recommendations...")
    extra_prog = st.progress(0, text="Processing WS/AS/FW...")
    extra_live = st.empty()

    try:
        def a2_extra_cb(pct, msg):
            extra_prog.progress(min(pct, 1.0), text=msg)
            extra_live.caption(f"↳ {msg}")

        new_ws = agent2.generate_generic_recommendations(
            st.session_state.ws_df, "WS", "Web Server", progress_callback=a2_extra_cb)
        st.session_state.ws_df = new_ws

        new_as = agent2.generate_generic_recommendations(
            st.session_state.as_df, "AS", "App Server", progress_callback=a2_extra_cb)
        st.session_state.as_df = new_as

        new_fw = agent2.generate_generic_recommendations(
            st.session_state.fw_df, "FW", "Framework", progress_callback=a2_extra_cb)
        st.session_state.fw_df = new_fw

        ws_f = (new_ws["Recommendation"] != "").sum()
        as_f = (new_as["Recommendation"] != "").sum()
        fw_f = (new_fw["Recommendation"] != "").sum()
        chk35.success(f"✅ **Checkpoint 3.5/4 PASSED** — WS: {ws_f}/{len(new_ws)} · "
                      f"AS: {as_f}/{len(new_as)} · FW: {fw_f}/{len(new_fw)} recommendations filled")
    except Exception as e:
        chk35.warning(f"⚠️ WS/AS/FW recommendations partial: `{e}`")

    # ── Checkpoint 4: Summary ─────────────────────────────────────────────────
    os_filled = (st.session_state.os_df["Recommendation"] != "").sum()
    db_filled = (st.session_state.db_df["Recommendation"] != "").sum()
    total     = os_filled + db_filled
    now       = datetime.now()
    save_app_state("last_refresh", now.isoformat())
    save_app_state("a2_last_run",  now.isoformat())
    st.success(
        f"✅ **Checkpoint 4/4 — Agent 2 COMPLETE** | "
        f"OS: {os_filled}/{len(st.session_state.os_df)} rows | "
        f"DB: {db_filled}/{len(st.session_state.db_df)} rows | "
        f"Total: **{total} recommendations** · 💾 **Persisted to database**"
    )
    st.session_state.a2_status = "done"
    if st.session_state.last_refresh is None:
        st.session_state.last_refresh = now

    st.rerun()


# ── Main content: Tabs OR Strategist ──────────────────────────────────────────
_show_strategist = st.session_state.get("show_strategist", False)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_dash, tab_os, tab_db, tab_ws, tab_as, tab_fw = st.tabs([
    "📊 Dashboard", "🖥️ OS Versions", "🗄️ DB Versions",
    "🌐 Web Servers", "⚙️ App Servers", "📦 Frameworks",
])

if _show_strategist:
    # Hide tabs entirely with CSS — Strategist renders below
    st.markdown("""<style>
    .stTabs { display: none !important; }
    </style>""", unsafe_allow_html=True)
    # Also hide download section when Strategist is open
    st.markdown("""<style>
    [data-testid="stDownloadButton"] { display: none !important; }
    </style>""", unsafe_allow_html=True)


# ────────────────── Tab 0: Executive Dashboard ────────────────────────────────
with tab_dash:
    st.subheader("📊 Executive Risk Dashboard")
    st.caption("Real-time risk analysis across your entire OS, DB, Web Server, App Server & Framework portfolio")

    # Top-level KPI metrics
    os_df_d = st.session_state.os_df
    db_df_d = st.session_state.db_df
    risk_summary = get_risk_summary(os_df_d, db_df_d)
    total_items = len(os_df_d) + len(db_df_d) + len(st.session_state.ws_df) + len(st.session_state.as_df) + len(st.session_state.fw_df)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: st.metric("Total Portfolio", total_items)
    with k2: st.metric("🔴 Critical", risk_summary["CRITICAL"])
    with k3: st.metric("🟠 High", risk_summary["HIGH"])
    with k4: st.metric("🟡 Medium", risk_summary["MEDIUM"])
    with k5: st.metric("🟢 Low", risk_summary["LOW"])
    with k6: st.metric("✅ Minimal", risk_summary["MINIMAL"])

    st.divider()

    # Charts row 1
    ch1, ch2 = st.columns(2)
    with ch1:
        fig_risk = risk_distribution_chart(os_df_d, db_df_d)
        st.plotly_chart(fig_risk, use_container_width=True)
    with ch2:
        fig_bar = status_breakdown_chart(os_df_d, db_df_d)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # EOL Timeline
    fig_timeline = eol_timeline_chart(os_df_d, db_df_d)
    st.plotly_chart(fig_timeline, use_container_width=True)

    st.divider()

    # Top urgent items table
    ch3, ch4 = st.columns([3, 2])
    with ch3:
        st.subheader("🚨 Top 10 Most Urgent Items")
        urgent = top_urgent_items(os_df_d, db_df_d, n=10)
        if not urgent.empty:
            st.dataframe(urgent, height=380, hide_index=True, use_container_width=True)
        else:
            st.info("Risk scores not yet computed.")
    with ch4:
        fig_hist = risk_score_histogram(os_df_d, db_df_d)
        st.plotly_chart(fig_hist, use_container_width=True)

    # Quick filter: items expiring during project window
    st.divider()
    st.subheader("⚠️ Items Expiring During Project Window")
    from datetime import date as _date
    proj_end = get_project_end()
    proj_start = st.session_state.get("project_start", _date(2026, 4, 1))
    expiring_os = os_df_d[
        os_df_d["Days Until EOL"].apply(
            lambda d: d is not None and 0 < d <= (proj_end - _date.today()).days
        )
    ] if "Days Until EOL" in os_df_d.columns else pd.DataFrame()
    expiring_db = db_df_d[
        db_df_d["Days Until EOL"].apply(
            lambda d: d is not None and 0 < d <= (proj_end - _date.today()).days
        )
    ] if "Days Until EOL" in db_df_d.columns else pd.DataFrame()

    exp_count = len(expiring_os) + len(expiring_db)
    if exp_count > 0:
        st.warning(f"**{exp_count} items** have support ending before {proj_end.strftime('%d %b %Y')}")
        ex1, ex2 = st.columns(2)
        with ex1:
            if not expiring_os.empty:
                st.caption(f"OS: {len(expiring_os)} items expiring")
                show_cols = [c for c in ["OS Version", "Days Until EOL", "Risk Score", "Risk Level", "Recommendation"] if c in expiring_os.columns]
                st.dataframe(expiring_os[show_cols].sort_values("Days Until EOL"), hide_index=True, height=250)
        with ex2:
            if not expiring_db.empty:
                st.caption(f"DB: {len(expiring_db)} items expiring")
                show_cols = [c for c in ["Database", "Version", "Days Until EOL", "Risk Score", "Risk Level", "Recommendation"] if c in expiring_db.columns]
                st.dataframe(expiring_db[show_cols].sort_values("Days Until EOL"), hide_index=True, height=250)
    else:
        st.success("No items expiring during the project window.")


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
    # Global search filter
    gs = st.session_state.get("global_search", "").strip()
    if gs:
        view = view[view.apply(lambda r: gs.lower() in " ".join(str(v) for v in r.values).lower(), axis=1)]
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
    if "Risk Score" in view.columns:
        disp["Risk Score"] = st.column_config.NumberColumn("🎯 Risk", width=70)
    if "Risk Level" in view.columns:
        disp["Risk Level"] = st.column_config.TextColumn("Risk Level", width=90)
    if "Days Until EOL" in view.columns:
        disp["Days Until EOL"] = st.column_config.NumberColumn("📅 Days to EOL", width=100)
    if "Policy Recommendation" in view.columns:
        disp["Policy Recommendation"] = st.column_config.TextColumn("🏛️ Policy Rec", width=360)
    if "Verdict" in view.columns:
        disp["Verdict"] = st.column_config.TextColumn("Verdict", width=120)
    # Hide internal color column
    hide_cols = [c for c in ["Risk Color"] if c in view.columns]
    if hide_cols:
        view = view.drop(columns=hide_cols)

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
    # Global search filter
    gs = st.session_state.get("global_search", "").strip()
    if gs:
        view_db = view_db[view_db.apply(lambda r: gs.lower() in " ".join(str(v) for v in r.values).lower(), axis=1)]
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
    if "Risk Score" in view_db.columns:
        db_disp["Risk Score"] = st.column_config.NumberColumn("🎯 Risk", width=70)
    if "Risk Level" in view_db.columns:
        db_disp["Risk Level"] = st.column_config.TextColumn("Risk Level", width=90)
    if "Days Until EOL" in view_db.columns:
        db_disp["Days Until EOL"] = st.column_config.NumberColumn("📅 Days to EOL", width=100)
    if "Policy Recommendation" in view_db.columns:
        db_disp["Policy Recommendation"] = st.column_config.TextColumn("🏛️ Policy Rec", width=360)
    if "Verdict" in view_db.columns:
        db_disp["Verdict"] = st.column_config.TextColumn("Verdict", width=120)
    # Hide internal color column
    hide_cols = [c for c in ["Risk Color"] if c in view_db.columns]
    if hide_cols:
        view_db = view_db.drop(columns=hide_cols)

    st.caption(f"Showing {len(view_db)} of {len(db_df)} DB entries")
    st.dataframe(
        view_db.style.map(_style_status, subset=["Status"]) if "Status" in view_db.columns else view_db,
        width="stretch", height=520, hide_index=True, column_config=db_disp
    )


# ────────────────── Tab: Web Servers ───────────────────────────────────────────
with tab_ws:
    ws_df = st.session_state.ws_df
    st.subheader("🌐 Web Server Versions")
    st.caption("Lifecycle tracking for IIS, Nginx, Apache and other web servers")

    wm1, wm2, wm3, wm4 = st.columns(4)
    eol_ws = (ws_df.get("Status", pd.Series(dtype=str)).str.lower() == "end of life").sum()
    exp_ws = (ws_df.get("Status", pd.Series(dtype=str)).str.lower() == "expiring soon").sum()
    sup_ws = (ws_df.get("Status", pd.Series(dtype=str)).str.lower() == "supported").sum()
    with wm1: st.metric("Total Web Servers", len(ws_df))
    with wm2: st.metric("🔴 End of Life", int(eol_ws))
    with wm3: st.metric("🟡 Expiring Soon", int(exp_ws))
    with wm4: st.metric("🟢 Supported", int(sup_ws))

    with st.expander("🔍 Filters", expanded=False):
        wf1, wf2, wf3 = st.columns(3)
        with wf1:
            ws_names = ["All"] + sorted(ws_df["Web Server"].dropna().unique().tolist())
            ws_f = st.selectbox("Web Server", ws_names, key="ws_filter")
        with wf2:
            ws_statuses = ["All"] + sorted(ws_df["Status"].dropna().unique().tolist())
            ws_stat_f = st.selectbox("Status", ws_statuses, key="ws_stat_filter")
        with wf3:
            ws_upg_f = st.selectbox("Upgrade", ["All","Y","N"], key="ws_upg_filter")

    view_ws = ws_df.copy()
    if ws_f != "All": view_ws = view_ws[view_ws["Web Server"] == ws_f]
    if ws_stat_f != "All": view_ws = view_ws[view_ws["Status"] == ws_stat_f]
    if ws_upg_f != "All": view_ws = view_ws[view_ws.get("Upgrade", pd.Series(dtype=str)) == ws_upg_f]

    def _style_ws_status(val):
        m = {"end of life": "background-color:#FFCDD2;color:#B71C1C",
             "expiring soon": "background-color:#FFE0B2;color:#E65100",
             "supported": "background-color:#C8E6C9;color:#1B5E20"}
        return m.get(str(val).lower(), "")

    ws_disp = {
        "Web Server": st.column_config.TextColumn("Web Server", width=140),
        "Version": st.column_config.TextColumn("Version", width=100),
        "Type": st.column_config.TextColumn("Type", width=120),
        "Mainstream / Premier End": st.column_config.TextColumn("Mainstream End", width=130),
        "Extended Support End": st.column_config.TextColumn("Extended End", width=120),
        "Status": st.column_config.TextColumn("Status", width=120),
        "Notes": st.column_config.TextColumn("Notes", width=220),
        "Recommendation": st.column_config.TextColumn("💡 Recommendation", width=360),
        "Upgrade": st.column_config.TextColumn("⬆ Upgrade", width=80),
        "Replace": st.column_config.TextColumn("🔁 Replace", width=80),
        "Primary Alternative": st.column_config.TextColumn("Primary Alt", width=150),
    }
    if "Risk Score" in view_ws.columns:
        ws_disp["Risk Score"] = st.column_config.NumberColumn("🎯 Risk", width=70)
    if "Risk Level" in view_ws.columns:
        ws_disp["Risk Level"] = st.column_config.TextColumn("Risk Level", width=90)
    if "Days Until EOL" in view_ws.columns:
        ws_disp["Days Until EOL"] = st.column_config.NumberColumn("📅 Days to EOL", width=100)
    hide_cols = [c for c in ["Risk Color"] if c in view_ws.columns]
    if hide_cols: view_ws = view_ws.drop(columns=hide_cols)

    st.caption(f"Showing {len(view_ws)} of {len(ws_df)} Web Server entries")
    st.dataframe(
        view_ws.style.map(_style_ws_status, subset=["Status"]) if "Status" in view_ws.columns else view_ws,
        width="stretch", height=520, hide_index=True, column_config=ws_disp
    )


# ────────────────── Tab: Application Servers ──────────────────────────────────
with tab_as:
    as_df = st.session_state.as_df
    st.subheader("⚙️ Application Server Versions")
    st.caption("Lifecycle tracking for Tomcat, JBoss, WebSphere, Kafka, RabbitMQ, Kubernetes and more")

    am1, am2, am3, am4 = st.columns(4)
    eol_as = (as_df.get("Status", pd.Series(dtype=str)).str.lower() == "end of life").sum()
    exp_as = (as_df.get("Status", pd.Series(dtype=str)).str.lower() == "expiring soon").sum()
    sup_as = (as_df.get("Status", pd.Series(dtype=str)).str.lower() == "supported").sum()
    with am1: st.metric("Total App Servers", len(as_df))
    with am2: st.metric("🔴 End of Life", int(eol_as))
    with am3: st.metric("🟡 Expiring Soon", int(exp_as))
    with am4: st.metric("🟢 Supported", int(sup_as))

    with st.expander("🔍 Filters", expanded=False):
        af1, af2, af3 = st.columns(3)
        with af1:
            as_names = ["All"] + sorted(as_df["App Server"].dropna().unique().tolist())
            as_f = st.selectbox("App Server", as_names, key="as_filter")
        with af2:
            as_types = ["All"] + sorted(as_df["Type"].dropna().unique().tolist())
            as_type_f = st.selectbox("Type", as_types, key="as_type_filter")
        with af3:
            as_statuses = ["All"] + sorted(as_df["Status"].dropna().unique().tolist())
            as_stat_f = st.selectbox("Status", as_statuses, key="as_stat_filter")

    view_as = as_df.copy()
    if as_f != "All": view_as = view_as[view_as["App Server"] == as_f]
    if as_type_f != "All": view_as = view_as[view_as["Type"] == as_type_f]
    if as_stat_f != "All": view_as = view_as[view_as["Status"] == as_stat_f]

    def _style_as_status(val):
        m = {"end of life": "background-color:#FFCDD2;color:#B71C1C",
             "expiring soon": "background-color:#FFE0B2;color:#E65100",
             "supported": "background-color:#C8E6C9;color:#1B5E20"}
        return m.get(str(val).lower(), "")

    as_disp = {
        "App Server": st.column_config.TextColumn("App Server", width=160),
        "Version": st.column_config.TextColumn("Version", width=100),
        "Type": st.column_config.TextColumn("Type", width=160),
        "Mainstream / Premier End": st.column_config.TextColumn("Mainstream End", width=130),
        "Extended Support End": st.column_config.TextColumn("Extended End", width=120),
        "Status": st.column_config.TextColumn("Status", width=120),
        "Notes": st.column_config.TextColumn("Notes", width=220),
        "Recommendation": st.column_config.TextColumn("💡 Recommendation", width=360),
        "Upgrade": st.column_config.TextColumn("⬆ Upgrade", width=80),
        "Replace": st.column_config.TextColumn("🔁 Replace", width=80),
        "Primary Alternative": st.column_config.TextColumn("Primary Alt", width=150),
    }
    if "Risk Score" in view_as.columns:
        as_disp["Risk Score"] = st.column_config.NumberColumn("🎯 Risk", width=70)
    if "Risk Level" in view_as.columns:
        as_disp["Risk Level"] = st.column_config.TextColumn("Risk Level", width=90)
    if "Days Until EOL" in view_as.columns:
        as_disp["Days Until EOL"] = st.column_config.NumberColumn("📅 Days to EOL", width=100)
    hide_cols = [c for c in ["Risk Color"] if c in view_as.columns]
    if hide_cols: view_as = view_as.drop(columns=hide_cols)

    st.caption(f"Showing {len(view_as)} of {len(as_df)} App Server entries")
    st.dataframe(
        view_as.style.map(_style_as_status, subset=["Status"]) if "Status" in view_as.columns else view_as,
        width="stretch", height=520, hide_index=True, column_config=as_disp
    )


# ────────────────── Tab: Frameworks ───────────────────────────────────────────
with tab_fw:
    fw_df = st.session_state.fw_df
    st.subheader("📦 Framework & Runtime Versions")
    st.caption("Lifecycle tracking for .NET, React, Angular, Spring Boot, Node.js, Java, Python, PHP and more")

    fm1, fm2, fm3, fm4 = st.columns(4)
    eol_fw = (fw_df.get("Status", pd.Series(dtype=str)).str.lower() == "end of life").sum()
    exp_fw = (fw_df.get("Status", pd.Series(dtype=str)).str.lower() == "expiring soon").sum()
    sup_fw = (fw_df.get("Status", pd.Series(dtype=str)).str.lower() == "supported").sum()
    with fm1: st.metric("Total Frameworks", len(fw_df))
    with fm2: st.metric("🔴 End of Life", int(eol_fw))
    with fm3: st.metric("🟡 Expiring Soon", int(exp_fw))
    with fm4: st.metric("🟢 Supported", int(sup_fw))

    with st.expander("🔍 Filters", expanded=False):
        ff1, ff2, ff3 = st.columns(3)
        with ff1:
            fw_names = ["All"] + sorted(fw_df["Framework"].dropna().unique().tolist())
            fw_f = st.selectbox("Framework", fw_names, key="fw_filter")
        with ff2:
            fw_types = ["All"] + sorted(fw_df["Type"].dropna().unique().tolist())
            fw_type_f = st.selectbox("Type", fw_types, key="fw_type_filter")
        with ff3:
            fw_statuses = ["All"] + sorted(fw_df["Status"].dropna().unique().tolist())
            fw_stat_f = st.selectbox("Status", fw_statuses, key="fw_stat_filter")

    view_fw = fw_df.copy()
    if fw_f != "All": view_fw = view_fw[view_fw["Framework"] == fw_f]
    if fw_type_f != "All": view_fw = view_fw[view_fw["Type"] == fw_type_f]
    if fw_stat_f != "All": view_fw = view_fw[view_fw["Status"] == fw_stat_f]

    def _style_fw_status(val):
        m = {"end of life": "background-color:#FFCDD2;color:#B71C1C",
             "expiring soon": "background-color:#FFE0B2;color:#E65100",
             "supported": "background-color:#C8E6C9;color:#1B5E20",
             "future": "background-color:#E3F2FD;color:#0D47A1"}
        return m.get(str(val).lower(), "")

    fw_disp = {
        "Framework": st.column_config.TextColumn("Framework", width=160),
        "Version": st.column_config.TextColumn("Version", width=120),
        "Type": st.column_config.TextColumn("Type", width=160),
        "Mainstream / Premier End": st.column_config.TextColumn("Mainstream End", width=130),
        "Extended Support End": st.column_config.TextColumn("Extended End", width=120),
        "Status": st.column_config.TextColumn("Status", width=120),
        "Notes": st.column_config.TextColumn("Notes", width=220),
        "Recommendation": st.column_config.TextColumn("💡 Recommendation", width=360),
        "Upgrade": st.column_config.TextColumn("⬆ Upgrade", width=80),
        "Replace": st.column_config.TextColumn("🔁 Replace", width=80),
        "Primary Alternative": st.column_config.TextColumn("Primary Alt", width=150),
    }
    if "Risk Score" in view_fw.columns:
        fw_disp["Risk Score"] = st.column_config.NumberColumn("🎯 Risk", width=70)
    if "Risk Level" in view_fw.columns:
        fw_disp["Risk Level"] = st.column_config.TextColumn("Risk Level", width=90)
    if "Days Until EOL" in view_fw.columns:
        fw_disp["Days Until EOL"] = st.column_config.NumberColumn("📅 Days to EOL", width=100)
    hide_cols = [c for c in ["Risk Color"] if c in view_fw.columns]
    if hide_cols: view_fw = view_fw.drop(columns=hide_cols)

    st.caption(f"Showing {len(view_fw)} of {len(fw_df)} Framework entries")
    st.dataframe(
        view_fw.style.map(_style_fw_status, subset=["Status"]) if "Status" in view_fw.columns else view_fw,
        width="stretch", height=520, hide_index=True, column_config=fw_disp
    )


# ────────────────── Strategist Panel (shown when toggled from sidebar) ─────────
if _show_strategist:
    if st.button("✕ Close Strategist — Back to Tabs", use_container_width=True):
        st.session_state["show_strategist"] = False
        st.rerun()
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
                padding:1.2rem 1.8rem;border-radius:12px;color:white;margin-bottom:1.5rem;">
      <h2 style="margin:0;font-size:1.3rem;font-weight:700;">
        🧠 Agent 5 — Policy Analysis &amp; Migration Intelligence
      </h2>
      <p style="margin:4px 0 0;font-size:0.8rem;opacity:0.8;">
        Project: <strong>1 Apr 2026 → 30 Jun 2028</strong> &nbsp;·&nbsp;
        Chat with Agent 5 → It collects your policy context → Generates Final Recommendations sheet
      </p>
    </div>""", unsafe_allow_html=True)

    if not key_ok:
        st.warning("⚠️ Enter your OpenAI API key in the sidebar to use Agent 5.")
    else:
        a5s = st.session_state.get("a5_status", "idle")

        # ── Progress stepper ──────────────────────────────────────────────────
        steps    = ["🗺️ Landscape", "☁️ Cloud", "📋 Principles", "💬 Policy Chat", "⚖️ GP Generate", "💰 Cost Intel", "🧠 Analysis", "✅ Complete"]
        step_map = {"idle":0,"landscape":0,"landscape_other":0,
                    "cloud_profile":1,"cloud_other":1,
                    "principles_table":2,
                    "chatting":3,"principles":4,"costing":5,
                    "ready":5,"analysing":6,"done":7}
        cur_step = step_map.get(a5s, 0)
        s_cols   = st.columns(len(steps))
        for i, (col, lbl) in enumerate(zip(s_cols, steps)):
            with col:
                if i < cur_step:
                    st.markdown(f"<div style='text-align:center;color:#10B981;font-size:0.8rem;'>✅ {lbl}</div>", unsafe_allow_html=True)
                elif i == cur_step:
                    st.markdown(f"<div style='text-align:center;color:#F59E0B;font-weight:700;font-size:0.8rem;'>● {lbl}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:center;color:#94A3B8;font-size:0.8rem;'>○ {lbl}</div>", unsafe_allow_html=True)
        st.divider()

        # ── PHASE 0: LANDSCAPE SURVEY ────────────────────────────────────────
        if a5s in ("idle", "landscape"):
            from agents.agent_analysis import categorize_os_families, get_family_display

            # Categorize OS families from live data
            os_families = categorize_os_families(st.session_state.os_df)
            st.session_state.a5_landscape_families = os_families

            st.markdown("""
            <div style="background:linear-gradient(135deg,#EFF6FF,#F0FDF4);
                        border:1px solid #BFDBFE;border-radius:12px;
                        padding:1.2rem 1.4rem;margin-bottom:1rem;">
              <h3 style="margin:0 0 0.5rem;color:#1E40AF;font-size:1.05rem;">
                🗺️ OS Landscape Survey
              </h3>
              <p style="margin:0;color:#374151;font-size:0.88rem;">
                I have categorized your OS landscape into <strong>""" + str(len([f for f in os_families if f != "Other"])) + """ primary families</strong>
                to simplify our modernization strategy.<br>
                <strong>Are all of the following currently present in your active IT landscape?</strong><br>
                <em>Please indicate any families that are NOT in scope for this exercise.</em>
              </p>
            </div>""", unsafe_allow_html=True)

            if a5s == "idle":
                st.session_state.a5_status = "landscape"
                st.rerun()

            # Display family checkboxes
            family_display = get_family_display()
            selected = []

            with st.form("landscape_form"):
                for fam_name, desc, emoji in family_display:
                    count = len(os_families.get(fam_name, []))
                    if fam_name == "Other":
                        # Always show Other option
                        versions_preview = ""
                        default = False
                    else:
                        if count == 0:
                            continue  # Skip families with no entries in our baseline
                        versions_preview = ", ".join(os_families[fam_name][:4])
                        if count > 4:
                            versions_preview += f" + {count - 4} more"
                        default = True

                    col1, col2 = st.columns([1, 4])
                    with col1:
                        checked = st.checkbox(
                            f"{emoji} {fam_name}",
                            value=default,
                            key=f"ls_{fam_name}"
                        )
                    with col2:
                        st.markdown(
                            f"<small style='color:#6B7280;'>{desc}"
                            + (f" — <em>{versions_preview}</em>" if versions_preview else "")
                            + f" ({count} tracked)</small>",
                            unsafe_allow_html=True
                        )
                    if checked:
                        selected.append(fam_name)

                st.divider()
                submitted = st.form_submit_button(
                    "✅ Confirm Landscape → Proceed to Policy Chat",
                    type="primary", use_container_width=True)

            if submitted:
                st.session_state.a5_landscape_selected = selected
                if "Other" in selected:
                    st.session_state.a5_status = "landscape_other"
                else:
                    # Store landscape context for the cloud profile phase
                    st.session_state.a5_context["os_landscape"] = ", ".join(
                        [f for f in selected if f != "Other"])
                    st.session_state.a5_status = "cloud_profile"
                st.rerun()

        # ── PHASE 0b: OTHER OS HANDLING ──────────────────────────────────────
        elif a5s == "landscape_other":
            from agents.agent_analysis import categorize_os_families

            st.markdown("""
            <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:12px;
                        padding:1rem 1.2rem;margin-bottom:1rem;">
              <h3 style="margin:0 0 0.4rem;color:#92400E;font-size:1rem;">
                ❓ You selected "Other" — Tell us about your additional OS
              </h3>
              <p style="margin:0;color:#78716C;font-size:0.85rem;">
                Please describe the OS that is missing from our list.
                Agent 5 will check if we already track it under a different name,
                or if it needs to be added to our baseline.
              </p>
            </div>""", unsafe_allow_html=True)

            other_input = st.text_input(
                "What OS is missing from the list?",
                placeholder="e.g. Gentoo Linux, Arch Linux, Chrome OS Flex...",
                key="a5_other_os_input"
            )

            if st.button("🔍 Verify OS", type="primary", disabled=not (key_ok and other_input)):
                with st.spinner("🧠 Agent 5 is checking if this OS is already tracked..."):
                    agent5 = PolicyAnalysisAgent(api_key=api_key)
                    result = agent5.verify_unknown_os(other_input, st.session_state.os_df)

                if result.get("match_found"):
                    st.success(
                        f"✅ **Match found!** \"{other_input}\" is already tracked as "
                        f"**{result.get('matched_to', '?')}** in our baseline.\n\n"
                        f"_{result.get('explanation', '')}_"
                    )
                    st.info("No changes needed. Click below to proceed.")
                    if st.button("➡️ Proceed to Cloud Profile", key="proceed_after_match"):
                        st.session_state.a5_context["os_landscape"] = ", ".join(
                            [f for f in st.session_state.a5_landscape_selected if f != "Other"])
                        st.session_state.a5_status = "cloud_profile"
                        st.rerun()

                elif result.get("is_valid_os"):
                    os_name = result.get("os_name", other_input)
                    st.warning(
                        f"🆕 **New OS detected:** **{os_name}** is a valid OS not in our baseline.\n\n"
                        f"_{result.get('explanation', '')}_\n\n"
                        f"**Agent 1 (Sentinel) will be triggered** to fetch lifecycle data for this OS."
                    )
                    if st.button("🚀 Add OS & Re-scan with Agent 1", type="primary", key="trigger_a1"):
                        # Add placeholder to baseline
                        import pandas as pd
                        new_row = {
                            "OS Version": os_name,
                            "Availability Date": "",
                            "Security/Standard Support End": "",
                            "Mainstream/Full Support End": "",
                            "Extended/LTSC Support End": "",
                            "Notes": f"Added by Agent 5 landscape survey — {datetime.now().strftime('%d %b %Y')}",
                            "Recommendation": "",
                            "Upgrade": "N", "Replace": "N",
                            "Primary Alternative": "", "Secondary Alternative": ""
                        }
                        st.session_state.os_df = pd.concat(
                            [st.session_state.os_df, pd.DataFrame([new_row])],
                            ignore_index=True)
                        st.session_state.os_df = add_risk_scores(st.session_state.os_df, "OS")

                        # Trigger Agent 1 for a focused scan
                        st.session_state.a1_status = "running"
                        with st.spinner(f"🔍 Agent 1 scanning lifecycle data for {os_name}..."):
                            try:
                                agent1 = OSDataAgent(api_key=api_key)
                                updates = agent1.fetch_updates(progress_callback=lambda p, m: None)
                                new_os, new_db, new_ws, new_as, new_fw, changes = agent1.merge_updates_into_df(
                                    st.session_state.os_df, st.session_state.db_df, updates,
                                    ws_df=st.session_state.ws_df,
                                    as_df=st.session_state.as_df,
                                    fw_df=st.session_state.fw_df)
                                st.session_state.os_df = add_risk_scores(new_os, "OS")
                                st.session_state.db_df = add_risk_scores(new_db, "DB")
                                st.session_state.ws_df = add_risk_scores(new_ws, "DB")
                                st.session_state.as_df = add_risk_scores(new_as, "DB")
                                st.session_state.fw_df = add_risk_scores(new_fw, "DB")
                                st.session_state.changes_log = changes
                                st.session_state.a1_status = "done"
                                save_os_df(st.session_state.os_df)
                                save_db_df(st.session_state.db_df)
                            except Exception as e:
                                st.session_state.a1_status = "error"
                                st.error(f"Agent 1 error: {e}")

                        st.success(f"✅ **{os_name}** added. Returning to landscape survey to re-categorize...")
                        # Go back to landscape to re-categorize with the new OS
                        st.session_state.a5_status = "landscape"
                        import time; time.sleep(2)
                        st.rerun()
                else:
                    st.error(
                        f"❌ **\"{other_input}\" does not appear to be a recognized OS.**\n\n"
                        f"_{result.get('explanation', '')}_\n\n"
                        f"Please try again with a valid operating system name."
                    )

            st.divider()
            if st.button("⏭️ Skip — Proceed without adding", use_container_width=True):
                st.session_state.a5_context["os_landscape"] = ", ".join(
                    [f for f in st.session_state.a5_landscape_selected if f != "Other"])
                st.session_state.a5_status = "cloud_profile"
                st.rerun()

        # ── PHASE 0c: CLOUD PROFILE SELECTION ────────────────────────────────
        elif a5s in ("cloud_profile", "cloud_other"):
            from agents.agent_analysis import PolicyAnalysisAgent as _PA5

            st.markdown("""
            <div style="background:linear-gradient(135deg,#EFF6FF,#E0F2FE);
                        border:1px solid #93C5FD;border-radius:12px;
                        padding:1.2rem 1.4rem;margin-bottom:1rem;">
              <h3 style="margin:0 0 0.5rem;color:#1E3A8A;font-size:1.05rem;">
                ☁️ Cloud Target Profile
              </h3>
              <p style="margin:0;color:#374151;font-size:0.88rem;">
                <strong>Please select the profile that best describes your target environment.</strong><br>
                This helps Agent 5 tailor migration recommendations to your cloud strategy.
              </p>
            </div>""", unsafe_allow_html=True)

            # ── Standard profiles ────────────────────────────────────────────
            CLOUD_PROFILES = [
                ("Microsoft-Centric (Azure)",
                 "🔷",
                 "Optimized for **Windows Server** (2012–2025) and Active Directory. "
                 "Leverages Azure Hybrid Benefit to reuse your on-prem licenses.",
                 "Azure"),
                ("Linux & Scale (AWS)",
                 "🟠",
                 "Optimized for large **RHEL/RPM-based** footprints. "
                 "Uses Graviton (ARM) processors for 40% better price-performance on modern Linux.",
                 "AWS"),
                ("Container & Data (GCP)",
                 "🔵",
                 "Optimized for **Ubuntu/Debian** and Kubernetes (GKE). "
                 "Ideal for high-speed AI data pipelines and global private fiber networking.",
                 "GCP"),
                ("Database & Legacy Bridge (Oracle/OCI)",
                 "🔴",
                 "The best \"Native Home\" for **Oracle Linux and Solaris**. "
                 "Offers the most stable path for large Oracle Database backends.",
                 "OCI"),
                ("Sovereign-First (US Government / High-Reg)",
                 "🛡️",
                 "A **vendor-agnostic, compliance-driven path**. Choose this if your data MUST reside in "
                 "**FedRAMP High, ITAR, or CJIS** regions (e.g., AWS GovCloud or Azure Government) "
                 "regardless of which OS is running.",
                 "GovCloud"),
            ]

            # Add any custom profiles from previous "Other" additions
            custom_profiles = st.session_state.get("a5_custom_cloud_profiles", [])
            all_profiles = CLOUD_PROFILES + custom_profiles

            if a5s == "cloud_profile":
                with st.form("cloud_profile_form"):
                    selected_cloud = None
                    for i, (name, emoji, desc, key) in enumerate(all_profiles):
                        col1, col2 = st.columns([1, 10])
                        with col1:
                            checked = st.checkbox(f"{emoji}", key=f"cp_{key}", value=False)
                        with col2:
                            st.markdown(
                                f"**{name}**  \n"
                                f"<small style='color:#4B5563;'>{desc}</small>",
                                unsafe_allow_html=True)
                        if checked:
                            selected_cloud = (name, key)

                    # Other option
                    st.divider()
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        other_checked = st.checkbox("❓", key="cp_other", value=False)
                    with col2:
                        st.markdown(
                            "**Other Cloud Provider**  \n"
                            "<small style='color:#4B5563;'>Not listed above — I'll describe my cloud target</small>",
                            unsafe_allow_html=True)

                    st.divider()
                    submitted = st.form_submit_button(
                        "✅ Confirm Cloud Profile → Proceed to Policy Chat",
                        type="primary", use_container_width=True)

                if submitted:
                    if other_checked:
                        st.session_state.a5_status = "cloud_other"
                        st.rerun()
                    elif selected_cloud:
                        st.session_state.a5_context["cloud_provider"] = selected_cloud[0]
                        st.session_state.a5_context["cloud_key"] = selected_cloud[1]
                        st.session_state.a5_status = "principles_table"
                        st.rerun()
                    else:
                        st.warning("Please select at least one cloud profile, or choose Other.")

            # ── "Other" cloud handling ───────────────────────────────────────
            elif a5s == "cloud_other":
                st.markdown("""
                <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:12px;
                            padding:1rem 1.2rem;margin-bottom:1rem;">
                  <h4 style="margin:0 0 0.4rem;color:#92400E;font-size:0.95rem;">
                    ❓ Describe your cloud target
                  </h4>
                  <p style="margin:0;color:#78716C;font-size:0.82rem;">
                    Agent 5 will research this provider and create a tailored profile for your selection.
                  </p>
                </div>""", unsafe_allow_html=True)

                other_cloud = st.text_input(
                    "Which cloud provider or environment?",
                    placeholder="e.g. IBM Cloud, Alibaba Cloud, VMware on-prem, Hybrid multi-cloud...",
                    key="a5_other_cloud_input"
                )

                if st.button("🔍 Research & Add Profile", type="primary",
                             disabled=not (key_ok and other_cloud)):
                    with st.spinner(f"🧠 Agent 5 researching {other_cloud}..."):
                        try:
                            agent5 = PolicyAnalysisAgent(api_key=api_key)
                            resp = agent5.client.chat.completions.create(
                                model=agent5.model, max_tokens=400,
                                messages=[{"role": "user", "content":
                                    f"Create a brief cloud migration profile for: {other_cloud}\n\n"
                                    f"Return ONLY JSON:\n"
                                    f'{{\"name\": \"short profile name\", '
                                    f'\"emoji\": \"single emoji\", '
                                    f'\"description\": \"2-sentence description of strengths for OS migration, similar style to Azure/AWS/GCP profiles\", '
                                    f'\"key\": \"short_key\"}}'
                                }])
                            text = resp.choices[0].message.content.strip()
                            if "```" in text:
                                text = text.split("```json")[-1].split("```")[0] if "```json" in text \
                                       else text.split("```")[1].split("```")[0]
                            s, e = text.find("{"), text.rfind("}")
                            profile = json.loads(text[s:e+1]) if s != -1 and e > s else None
                        except Exception:
                            profile = None

                    if profile:
                        new_profile = (
                            profile.get("name", other_cloud),
                            profile.get("emoji", "☁️"),
                            profile.get("description", f"Custom profile for {other_cloud}"),
                            profile.get("key", other_cloud.lower().replace(" ", "_"))
                        )
                        custom = st.session_state.get("a5_custom_cloud_profiles", [])
                        custom.append(new_profile)
                        st.session_state.a5_custom_cloud_profiles = custom

                        st.success(
                            f"✅ **{new_profile[0]}** profile created!\n\n"
                            f"{new_profile[1]} {new_profile[2]}\n\n"
                            f"Returning to selection so you can choose it."
                        )
                        st.session_state.a5_status = "cloud_profile"
                        import time; time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Could not generate profile. Please try with a more specific cloud name.")

                st.divider()
                if st.button("⏭️ Skip — Use no specific cloud preference", use_container_width=True):
                    st.session_state.a5_context["cloud_provider"] = "No strong preference"
                    st.session_state.a5_status = "principles_table"
                    st.rerun()

        # ── PHASE 0d: GUIDING PRINCIPLES TABLE ──────────────────────────────
        elif a5s == "principles_table":
            from agents.agent_analysis import generate_principles_table

            st.markdown("""
            <div style="background:linear-gradient(135deg,#F0FDF4,#ECFDF5);
                        border:1px solid #A7F3D0;border-radius:12px;
                        padding:1.2rem 1.4rem;margin-bottom:1rem;">
              <h3 style="margin:0 0 0.5rem;color:#065F46;font-size:1.05rem;">
                📋 OS Migration Guiding Principles
              </h3>
              <p style="margin:0;color:#374151;font-size:0.88rem;">
                Based on your <strong>OS landscape</strong> and <strong>cloud profile</strong>,
                here are the guiding principles for your modernization strategy.
              </p>
            </div>""", unsafe_allow_html=True)

            selected_fams = st.session_state.get("a5_landscape_selected", [])
            cloud_name = st.session_state.get("a5_context", {}).get("cloud_provider", "No preference")
            cloud_key = st.session_state.get("a5_context", {}).get("cloud_key", "")

            # Generate or use cached table
            if "a5_principles_table_data" not in st.session_state:
                with st.spinner("🧠 Agent 5 generating tailored guiding principles..."):
                    try:
                        agent5 = PolicyAnalysisAgent(api_key=api_key)
                        table_data = generate_principles_table(
                            selected_fams, cloud_name, cloud_key, agent=agent5)
                    except Exception:
                        table_data = generate_principles_table(
                            selected_fams, cloud_name, cloud_key, agent=None)
                    st.session_state.a5_principles_table_data = table_data
                st.rerun()

            table_data = st.session_state.a5_principles_table_data

            if table_data:
                # Render as styled table
                st.markdown(
                    "<table style='width:100%;border-collapse:collapse;font-size:0.85rem;'>"
                    "<thead><tr style='background:#1E3A8A;color:white;'>"
                    "<th style='padding:10px 12px;text-align:left;border:1px solid #3B82F6;'>OS Family</th>"
                    "<th style='padding:10px 12px;text-align:left;border:1px solid #3B82F6;'>Cloud Target</th>"
                    "<th style='padding:10px 12px;text-align:left;border:1px solid #3B82F6;'>OS Upgrade Principle</th>"
                    "<th style='padding:10px 12px;text-align:left;border:1px solid #3B82F6;'>OS Replacement Principle</th>"
                    "</tr></thead><tbody>",
                    unsafe_allow_html=True)

                row_colors = ["#F8FAFC", "#EFF6FF"]
                for i, row in enumerate(table_data):
                    bg = row_colors[i % 2]
                    # Color-code upgrade vs replacement
                    upg = row.get("upgrade_principle", "")
                    repl = row.get("replacement_principle", "")
                    upg_color = "#166534" if "COTS" in upg else ("#92400E" if "None" in upg else "#1E40AF")
                    repl_color = "#7C2D12" if "Mandatory" in repl else "#4338CA"

                    st.markdown(
                        f"<tr style='background:{bg};'>"
                        f"<td style='padding:8px 12px;border:1px solid #E2E8F0;font-weight:600;'>"
                        f"{row.get('os_family', '')}</td>"
                        f"<td style='padding:8px 12px;border:1px solid #E2E8F0;color:#1D4ED8;'>"
                        f"{row.get('cloud_target', '')}</td>"
                        f"<td style='padding:8px 12px;border:1px solid #E2E8F0;color:{upg_color};'>"
                        f"{upg}</td>"
                        f"<td style='padding:8px 12px;border:1px solid #E2E8F0;color:{repl_color};'>"
                        f"{repl}</td>"
                        f"</tr>",
                        unsafe_allow_html=True)

                st.markdown("</tbody></table>", unsafe_allow_html=True)

                # Store in context for the policy chat
                st.session_state.a5_context["os_principles_table"] = json.dumps(table_data)

                st.divider()

                # Summary metrics
                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.metric("OS Families in Scope", len(table_data))
                with mc2:
                    upgrade_count = sum(1 for r in table_data if "Upgrade" in r.get("upgrade_principle", "") or "COTS" in r.get("upgrade_principle", ""))
                    st.metric("Upgrade Paths", upgrade_count)
                with mc3:
                    replace_count = sum(1 for r in table_data if "Replace" in r.get("replacement_principle", "") or "Mandatory" in r.get("replacement_principle", ""))
                    st.metric("Replacement Candidates", replace_count)

                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Accept Principles → Proceed to Policy Chat",
                                 type="primary", use_container_width=True):
                        st.session_state.a5_status = "chatting"
                        st.rerun()
                with col2:
                    if st.button("🔄 Regenerate with AI", use_container_width=True):
                        st.session_state.pop("a5_principles_table_data", None)
                        st.rerun()
            else:
                st.warning("No OS families selected. Go back to the Landscape Survey.")
                if st.button("⬅️ Back to Landscape Survey"):
                    st.session_state.a5_status = "landscape"
                    st.rerun()

        # ── PHASE 1: CHAT ─────────────────────────────────────────────────────
        elif a5s in ("chatting",):

            # Import SQLite helpers from agent
            from agents.agent_analysis import (
                _save_message, _load_messages, _save_session_context,
                _list_sessions, _delete_session
            )

            # Show past sessions in expander
            sessions = _list_sessions()
            if sessions:
                with st.expander(f"📂 Past conversations ({len(sessions)})", expanded=False):
                    for sess in sessions:
                        sc1, sc2, sc3 = st.columns([3, 1, 1])
                        with sc1:
                            st.markdown(
                                f"**{sess['session']}** — {sess['summary'][:60]}  \n"
                                f"<small>{sess['updated']} · {sess['status']}</small>",
                                unsafe_allow_html=True
                            )
                        with sc2:
                            if st.button("▶ Resume", key=f"res_{sess['session']}"):
                                st.session_state.a5_session_id = sess["session"]
                                st.session_state.a5_status     = sess["status"] if sess["status"] in ("chatting","ready","done") else "chatting"
                                st.rerun()
                        with sc3:
                            if st.button("🗑 Delete", key=f"del_{sess['session']}"):
                                _delete_session(sess["session"])
                                st.rerun()

            # Create session on first entry to chat phase
            session_id = PolicyAnalysisAgent.get_or_create_session()
            if not st.session_state.get("a5_opening_pending") and not _load_messages(session_id):
                st.session_state.a5_opening_pending = True
            messages   = _load_messages(session_id)

            # ── Show landscape context if available ──────────────────────────
            ls_selected = st.session_state.get("a5_landscape_selected", [])
            if ls_selected:
                active_fams = [f for f in ls_selected if f != "Other"]
                if active_fams:
                    st.markdown(
                        f"<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;"
                        f"padding:0.5rem 0.8rem;margin-bottom:0.8rem;font-size:0.82rem;color:#1E40AF;'>"
                        f"🗺️ <strong>OS Landscape:</strong> {' · '.join(active_fams)}"
                        f"</div>", unsafe_allow_html=True)

            # ── Welcome / guidance panel (shown only when chat is empty) ──────
            if not messages:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#EFF6FF,#F0FDF4);
                            border:1px solid #BFDBFE;border-radius:12px;
                            padding:1.4rem 1.6rem;margin-bottom:1.2rem;">
                  <h3 style="margin:0 0 0.6rem;color:#1E40AF;font-size:1.1rem;">
                    👋 Welcome to Agent 5 — Your Migration Policy Advisor
                  </h3>
                  <p style="margin:0 0 0.8rem;color:#374151;font-size:0.9rem;">
                    Agent 5 will guide you through a <strong>natural conversation</strong>
                    to define your organisation's migration policy for
                    <strong>Apr 2026 → Jun 2028</strong>. It adapts to your answers and
                    <strong>searches the internet in real-time</strong> for pricing,
                    ESU costs, migration guides and upgrade paths.
                  </p>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;margin-bottom:0.8rem;">
                    <div style="background:white;border-radius:8px;padding:0.6rem 0.8rem;border:1px solid #E5E7EB;">
                      <strong style="color:#1D4ED8;font-size:0.82rem;">💬 What to expect</strong><br>
                      <span style="font-size:0.8rem;color:#6B7280;">
                        10–15 focused questions about risk tolerance, budgets,
                        OS/DB migration paths, compliance scope and execution capacity.
                      </span>
                    </div>
                    <div style="background:white;border-radius:8px;padding:0.6rem 0.8rem;border:1px solid #E5E7EB;">
                      <strong style="color:#059669;font-size:0.82rem;">🔍 Real-time searches</strong><br>
                      <span style="font-size:0.8rem;color:#6B7280;">
                        Ask about ESU costs, cloud DB pricing, RHEL subscriptions,
                        Oracle support fees or any migration guide — it searches live.
                      </span>
                    </div>
                    <div style="background:white;border-radius:8px;padding:0.6rem 0.8rem;border:1px solid #E5E7EB;">
                      <strong style="color:#7C3AED;font-size:0.82rem;">⚖️ Guiding Principles</strong><br>
                      <span style="font-size:0.8rem;color:#6B7280;">
                        Your answers become 8–10 named Guiding Principles (GP-01…)
                        that govern every migration recommendation.
                      </span>
                    </div>
                    <div style="background:white;border-radius:8px;padding:0.6rem 0.8rem;border:1px solid #E5E7EB;">
                      <strong style="color:#DC2626;font-size:0.82rem;">📊 Final Recommendations</strong><br>
                      <span style="font-size:0.8rem;color:#6B7280;">
                        Cross-references Agent 2's technical advice with your policy
                        to produce a Final Recommendations sheet in Excel.
                      </span>
                    </div>
                  </div>
                  <p style="margin:0;color:#6B7280;font-size:0.8rem;">
                    💡 <strong>Tip:</strong> Answer in your own words — you don't need to follow a format.
                    You can also ask Agent 5 questions at any time, e.g.
                    <em>"What does Windows Server 2016 ESU cost?"</em> or
                    <em>"What's the best path to migrate Oracle to PostgreSQL?"</em>
                  </p>
                </div>
                """, unsafe_allow_html=True)

                # ── Starter prompts ───────────────────────────────────────────
                st.markdown("**🚀 Start with one of these, or type your own:**")
                starter_cols = st.columns(2)
                starters = [
                    ("🏢 Enterprise context",
                     "We are a large enterprise running a mix of Windows Server, RHEL, Oracle and SQL Server. We have PCI DSS compliance requirements and our priority is zero EOL risk for Tier-1 systems."),
                    ("💰 Cost-focused",
                     "Our budget is constrained. We need to know the real cost of extending support vs migrating. Can you help me understand the ESU pricing for Windows Server 2016 and SQL Server 2017?"),
                    ("☁️ Cloud migration",
                     "We are planning to migrate our SQL Server and Oracle databases to the cloud. Our preferred provider is Azure. What should I consider for the migration policy?"),
                    ("🔒 Compliance-led",
                     "We are under HIPAA and SOX compliance. Our risk tolerance for EOL software is zero for regulated systems. We have a small migration team of 5 people."),
                ]
                for i, (label, prompt_text) in enumerate(starters):
                    with starter_cols[i % 2]:
                        if st.button(label, key=f"starter_{i}", width="stretch",
                                     help=prompt_text[:80] + "..."):
                            _save_message(session_id, "user", prompt_text)
                            with st.spinner("🧠 Agent 5 is preparing your personalised policy session..."):
                                agent5   = PolicyAnalysisAgent(api_key=api_key)
                                all_msgs = _load_messages(session_id)
                                reply    = agent5.chat(all_msgs)
                                _save_message(session_id, "assistant", reply)
                                _save_session_context(session_id, {}, "", "chatting")
                            st.rerun()

                st.divider()

                # ── Generate opening message if not yet done ──────────────────
                if st.session_state.get("a5_opening_pending"):
                    with st.spinner("🧠 Agent 5 is preparing your session..."):
                        agent5  = PolicyAnalysisAgent(api_key=api_key)
                        opening = agent5.chat([])
                        _save_message(session_id, "assistant", opening)
                        st.session_state.a5_opening_pending = False
                    st.rerun()
                else:
                    if st.button("▶ Let Agent 5 start the conversation", type="primary",
                                 width="stretch"):
                        st.session_state.a5_opening_pending = True
                        st.rerun()

            else:
                # ── Show session info bar ─────────────────────────────────────
                st.markdown(
                    f"<div style='background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;"
                    f"padding:0.5rem 1rem;margin-bottom:0.8rem;font-size:0.82rem;color:#166534;'>"
                    f"💬 Session <strong>{session_id}</strong> · "
                    f"{len(messages)} message{'s' if len(messages) != 1 else ''} · "
                    f"🔍 Agent 5 searches the web in real-time for costs, pricing and migration guides"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # ── Render chat history ───────────────────────────────────────
                for msg in messages:
                    with st.chat_message(msg["role"],
                                         avatar="🧠" if msg["role"] == "assistant" else "👤"):
                        st.markdown(msg["content"])

            # ── User chat input (always shown when chatting) ──────────────────
            if messages or not st.session_state.get("a5_opening_pending"):
                if user_input := st.chat_input(
                    "Ask about ESU costs, migration options, compliance, or answer Agent 5's questions..."
                ):
                    _save_message(session_id, "user", user_input)
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(user_input)

                    with st.chat_message("assistant", avatar="🧠"):
                        with st.spinner("🔍 Agent 5 is thinking..."):
                            agent5   = PolicyAnalysisAgent(api_key=api_key)
                            all_msgs = _load_messages(session_id)
                            reply    = agent5.chat(all_msgs)

                        # Adaptive completion — accepts 4+ exchanges, fills defaults for gaps
                        done, context, summary, inferred = agent5.is_conversation_complete(
                            reply, message_count=len(all_msgs) + 1)

                        if done:
                            inferred_note = ""
                            if inferred:
                                inferred_note = (
                                    f"\n\n💡 **Topics using defaults** (not explicitly discussed): "
                                    f"{', '.join(inferred)}. "
                                    f"These can be refined by continuing the conversation."
                                )
                            complete_msg = (
                                f"✅ **I have enough policy context to proceed.**\n\n"
                                f"**Policy Summary:** {summary}"
                                f"{inferred_note}\n\n"
                                f"Moving to Phase 2 — generating Guiding Principles..."
                            )
                            st.markdown(complete_msg)
                            _save_message(session_id, "assistant", complete_msg)
                            _save_session_context(session_id, context, summary, "principles")
                            st.session_state.a5_context = context
                            st.session_state.a5_status  = "principles"
                        else:
                            st.markdown(reply)
                            _save_message(session_id, "assistant", reply)
                            _save_session_context(session_id, {}, "", "chatting")
                    st.rerun()

            # ── Topic coverage + controls ─────────────────────────────────────
            if messages:
                TOPIC_LABELS = {
                    "eol_tolerance": "EOL risk tolerance",  "min_runway": "Support runway",
                    "esu_budget": "ESU budget",             "compliance": "Compliance scope",
                    "windows_path": "Windows path",         "linux_path": "Linux/Unix path",
                    "db_eol_path": "DB EOL path",           "oracle_stance": "Oracle stance",
                    "cloud_provider": "Cloud provider",     "legacy_db": "Legacy DBs",
                    "capacity": "Migration capacity",        "criticality": "System priority",
                    "rollback": "Rollback policy",
                }
                saved_ctx = st.session_state.get("a5_context", {})
                explicit  = [k for k, l in TOPIC_LABELS.items()
                             if saved_ctx.get(k,"").strip() and not saved_ctx.get(k,"").startswith("[Default]")]
                msg_count = len(messages)
                pct       = int(len(explicit) / len(TOPIC_LABELS) * 100)

                if msg_count >= 8:
                    colour = "#F0FDF4"; border = "#BBF7D0"; text_c = "#166534"
                    note   = f"✅ {len(explicit)}/{len(TOPIC_LABELS)} topics explicitly covered"
                else:
                    colour = "#FFF7ED"; border = "#FED7AA"; text_c = "#92400E"
                    note   = f"💬 {len(explicit)}/{len(TOPIC_LABELS)} topics covered · keep chatting or proceed when ready"

                st.markdown(
                    f"<div style='background:{colour};border:1px solid {border};"
                    f"border-radius:8px;padding:0.5rem 0.9rem;font-size:0.8rem;color:{text_c};'>"
                    f"{note} · {msg_count} messages<br>"
                    f"<span style='color:#6B7280;font-size:0.75rem;'>"
                    f"Missing topics will use enterprise defaults — you can refine anytime</span>"
                    f"</div>", unsafe_allow_html=True)

                st.divider()
                col_proceed, col_reset = st.columns([2, 1])
                with col_proceed:
                    # Allow manual proceed after just 4 exchanges (8 messages)
                    if len(messages) >= 8:
                        if st.button("➡️ Proceed to Guiding Principles",
                                     type="primary", width="stretch"):
                            agent5     = PolicyAnalysisAgent(api_key=api_key)
                            all_msgs   = _load_messages(session_id)
                            ctx_prompt = (
                                "Extract all policy context discussed so far as JSON with these keys: "
                                "eol_tolerance, min_runway, esu_budget, compliance, "
                                "windows_path, linux_path, db_eol_path, oracle_stance, "
                                "cloud_provider, legacy_db, capacity, criticality, rollback. "
                                "For any topic NOT discussed, use '[Default] <sensible enterprise default>'. "
                                "Return ONLY the JSON object."
                            )
                            try:
                                r = agent5.client.chat.completions.create(
                                    model="gpt-4o-mini", max_tokens=700,
                                    messages=all_msgs + [{"role":"user","content":ctx_prompt}]
                                )
                                t = r.choices[0].message.content.strip()
                                s, e = t.find("{"), t.rfind("}")
                                context = json.loads(t[s:e+1]) if s != -1 and e > s else {}
                            except Exception:
                                context = {"note": "Extracted from conversation"}
                            _save_session_context(session_id, context, "Manual proceed", "principles")
                            st.session_state.a5_context = context
                            st.session_state.a5_status  = "principles"
                            st.rerun()
                    else:
                        remaining = max(0, 8 - len(messages))
                        st.caption(f"💬 {remaining} more message(s) before you can proceed manually")
                with col_reset:
                    if st.button("🔄 New Conversation", width="stretch"):
                        PolicyAnalysisAgent.reset()
                        st.rerun()

        # ── PHASE 2: Generate Principles ──────────────────────────────────────
        elif a5s == "principles":
            st.subheader("⚖️ Generating Guiding Principles from your policy conversation...")
            with st.spinner("OpenAI is synthesising your answers into Guiding Principles..."):
                session_id = PolicyAnalysisAgent.get_or_create_session()
                agent5     = PolicyAnalysisAgent(api_key=api_key)
                principles = agent5.generate_principles(
                    st.session_state.a5_context,
                    session_id
                )
                st.session_state.a5_principles = principles
                st.session_state.a5_status     = "costing"
            st.rerun()

        # ── PHASE 3: Cost Intelligence ─────────────────────────────────────────
        elif a5s == "costing":
            st.subheader("💰 Fetching Live Vendor Pricing...")
            st.caption("Agent 5 is searching the web for current ESU costs, cloud DB pricing, RHEL subscription rates and migration tool costs.")
            prog = st.progress(0, text="Searching live pricing...")
            stat = st.empty()
            def cost_cb(pct, msg):
                prog.progress(min(pct, 1.0), text=msg)
                stat.info(f"⏳ {msg}")
            agent5 = PolicyAnalysisAgent(api_key=api_key)
            costs  = agent5.fetch_costs(progress_cb=cost_cb)
            st.session_state.a5_costs  = costs
            st.session_state.a5_status = "ready"
            st.rerun()

        # ── PHASE 3 READY: Show principles + confirm ──────────────────────────
        elif a5s == "ready":
            principles = st.session_state.a5_principles
            context    = st.session_state.a5_context

            # Show policy summary from chat
            if context:
                with st.expander("📋 Policy Context from conversation", expanded=False):
                    for k, v in context.items():
                        is_default = str(v).startswith("[Default]")
                        icon = "⚙️" if is_default else "✅"
                        label = k.replace("_"," ").title()
                        st.markdown(f"{icon} **{label}:** {v}"
                                    + (" *(enterprise default — not discussed)*" if is_default else ""))

            with st.expander(f"⚖️ {len(principles)} Guiding Principles generated", expanded=True):
                c1, c2 = st.columns(2)
                cat_colors = {"Risk":"#EF4444","Budget":"#F59E0B","OS":"#3B82F6",
                              "Database":"#8B5CF6","Execution":"#10B981"}
                for i, gp in enumerate(principles):
                    cat   = gp.get("category","")
                    color = cat_colors.get(cat, "#6B7280")
                    with (c1 if i % 2 == 0 else c2):
                        st.markdown(
                            f"<div style='border-left:3px solid {color};padding:8px 12px;"
                            f"border-radius:0 6px 6px 0;background:rgba(0,0,0,0.03);margin-bottom:8px;'>"
                            f"<strong>{gp.get('code','?')}: {gp.get('title','?')}</strong> "
                            f"<span style='font-size:0.7rem;color:{color};background:rgba(0,0,0,0.06);"
                            f"padding:1px 6px;border-radius:8px;'>{cat}</span><br>"
                            f"<span style='font-size:0.82rem;'>{gp.get('rule','')}</span><br>"
                            f"<span style='font-size:0.75rem;color:#6B7280;'>Trigger: {gp.get('trigger','')}</span>"
                            f"</div>", unsafe_allow_html=True)

            with st.expander(f"💰 Vendor Cost Intelligence ({len(st.session_state.a5_costs)} sources)", expanded=False):
                for vendor, summary in st.session_state.a5_costs.items():
                    st.markdown(f"**{vendor}:** {summary}")

            st.divider()
            st.subheader("🚀 Ready to Generate Final Recommendations")

            a2_os = (st.session_state.os_df["Recommendation"] != "").sum()
            a2_db = (st.session_state.db_df["Recommendation"] != "").sum()
            total_rows = len(st.session_state.os_df) + len(st.session_state.db_df)

            if a2_os + a2_db == 0:
                st.warning("⚠️ Run Agent 2 first — Final Recommendations are richer when Agent 2's technical advice is available.")
            else:
                st.success(f"✅ Agent 2 recommendations available: {a2_os} OS + {a2_db} DB rows")

            st.info(
                f"Agent 5 will now cross-reference **{total_rows} entries** against your "
                f"**{len(principles)} Guiding Principles** and Agent 2's recommendations to produce "
                f"a **Final Recommendation** column — this will appear as a separate sheet in the Excel export."
            )

            if st.button("▶ Generate Final Recommendations", type="primary", width="stretch"):
                st.session_state.a5_status = "analysing"
                st.rerun()
            if st.button("💬 Continue the conversation / refine policy", width="stretch"):
                st.session_state.a5_status = "chatting"
                st.rerun()
            if st.button("🔄 Start Over", width="stretch"):
                PolicyAnalysisAgent.reset()
                st.rerun()

        # ── PHASE 4: Analysis ─────────────────────────────────────────────────
        elif a5s == "analysing":
            st.subheader("🧠 Agent 5 — Generating Final Recommendations...")

            if "a5_log" not in st.session_state:
                st.session_state.a5_log = []

            def _log(icon, msg):
                st.session_state.a5_log.append(f"{icon} {msg}")

            log_box = st.container()
            with log_box:
                for entry in st.session_state.a5_log:
                    if entry.startswith("❌"): st.error(entry)
                    elif entry.startswith("⚠️"): st.warning(entry)
                    elif entry.startswith("✅"): st.success(entry)
                    else: st.info(entry)

            prog_bar = st.progress(0, text="Starting...")
            st.divider()

            # Pre-flight
            if not st.session_state.get("a5_preflight_done"):
                _log("🔌", "**Step 1/4 — Testing OpenAI API connection...**")
                try:
                    from openai import OpenAI as _OAI
                    _client = _OAI(api_key=api_key)
                    # Try models in order until one works
                    _model_used = None
                    for _m in ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-3.5-turbo-0125"]:
                        try:
                            _resp = _client.chat.completions.create(
                                model=_m, max_tokens=10,
                                messages=[{"role":"user","content":"Reply: READY"}]
                            )
                            _model_used = _m
                            st.session_state["_openai_model"] = _m
                            break
                        except Exception as _me:
                            if "not found" in str(_me).lower() or "404" in str(_me):
                                continue
                            raise _me
                    if not _model_used:
                        raise Exception("No supported model found on this OpenAI account")
                    _reply = _resp.choices[0].message.content.strip()
                    _log("✅", f"**OpenAI API connected** — model: `{_model_used}` · response: **{_reply}**")
                    st.session_state.a5_preflight_done = True
                except Exception as _ex:
                    _log("❌", f"**OpenAI API FAILED** — `{str(_ex)}`\n\nCheck: platform.openai.com/usage")
                    with log_box: st.error(st.session_state.a5_log[-1])
                    st.stop()
                st.rerun()

            # Analysis steps: OS → DB → WS → AS → FW
            _a5_steps = [
                ("a5_os_done", "os_df", "OS", "analyse_os", 2),
                ("a5_db_done", "db_df", "DB", "analyse_db", 3),
                ("a5_ws_done", "ws_df", "WS", "analyse_ws", 4),
                ("a5_as_done", "as_df", "AS", "analyse_as", 5),
                ("a5_fw_done", "fw_df", "FW", "analyse_fw", 6),
            ]
            total_steps = len(_a5_steps) + 2  # +1 preflight, +1 wrapup = 7

            for done_key, df_key, kind_label, method_name, step_num in _a5_steps:
                if not st.session_state.get(done_key):
                    agent5     = PolicyAnalysisAgent(api_key=api_key)
                    principles = st.session_state.a5_principles
                    costs      = st.session_state.a5_costs
                    context    = st.session_state.a5_context
                    cur_df     = st.session_state[df_key]
                    _log("🧠", f"**Step {step_num}/{total_steps} — Final Recommendations for {len(cur_df)} {kind_label} entries...**")

                    _live = st.empty()
                    frac_start = (step_num - 2) / (total_steps - 2)
                    frac_end   = (step_num - 1) / (total_steps - 2)
                    def _make_cb(fs=frac_start, fe=frac_end):
                        def cb(pct, msg):
                            prog_bar.progress(min(fs + pct * (fe - fs), 1.0), text=msg)
                            _live.info(f"⏳ {msg}")
                        return cb

                    analyse_fn = getattr(agent5, method_name)
                    new_df = analyse_fn(cur_df, principles, costs, context, _make_cb())
                    st.session_state[df_key] = new_df
                    st.session_state[done_key] = True
                    # Persist OS/DB to SQLite
                    if df_key == "os_df":
                        save_os_df(new_df)
                    elif df_key == "db_df":
                        save_db_df(new_df)

                    if "Analysis Source" in new_df.columns:
                        ai_c = (new_df["Analysis Source"] == "OpenAI").sum()
                        rb_c = (new_df["Analysis Source"] == "Rule-based").sum()
                        _log("✅" if rb_c == 0 else "⚠️",
                             f"**{kind_label} done** — OpenAI: {ai_c} rows ✅" +
                             (f" | Rule-based fallback: {rb_c} rows" if rb_c else ""))
                    st.rerun()

            _log("🏁", f"**Step {total_steps}/{total_steps} — Final Recommendations complete for all categories.**")
            st.session_state.a5_status         = "done"
            st.session_state.a5_preflight_done = False
            st.session_state.a5_log            = []
            st.rerun()

        # ── PHASE 5: DONE ─────────────────────────────────────────────────────
        elif a5s == "done":
            st.success(
                "✅ **Agent 5 complete!** "
                "'Final Recommendation' and 'Final Verdict' columns added to OS and DB tabs. "
                "A dedicated **Final Recommendations** sheet is included in the Excel export."
            )

            os_df_now = st.session_state.os_df
            db_df_now = st.session_state.db_df

            # AI vs rule-based breakdown
            if "Analysis Source" in os_df_now.columns or "Analysis Source" in db_df_now.columns:
                ai_os = (os_df_now.get("Analysis Source", pd.Series(dtype=str)) == "OpenAI").sum() if "Analysis Source" in os_df_now.columns else 0
                rb_os = (os_df_now.get("Analysis Source", pd.Series(dtype=str)) == "Rule-based").sum() if "Analysis Source" in os_df_now.columns else 0
                ai_db = (db_df_now.get("Analysis Source", pd.Series(dtype=str)) == "OpenAI").sum() if "Analysis Source" in db_df_now.columns else 0
                rb_db = (db_df_now.get("Analysis Source", pd.Series(dtype=str)) == "Rule-based").sum() if "Analysis Source" in db_df_now.columns else 0
                total_ai = ai_os + ai_db; total_rb = rb_os + rb_db
                if total_ai > 0:
                    st.info(f"🤖 **OpenAI generated {total_ai} Final Recommendations** (OS: {ai_os}, DB: {ai_db}) "
                            f"| 📐 Rule-based fallback: {total_rb} rows")
                else:
                    st.warning("⚠️ OpenAI did not respond — all rows used rule-based analysis. Check API quota.")

            # Verdict summary
            verdicts = ["CRITICAL","UPGRADE NOW","EXTEND + PLAN","REPLACE","CLOUD MIGRATE","MONITOR"]
            fv_col = "Final Verdict"
            if fv_col in os_df_now.columns or fv_col in db_df_now.columns:
                st.subheader("📊 Final Verdict Summary")
                vcols = st.columns(6)
                for i, v in enumerate(verdicts):
                    os_c = int((os_df_now.get(fv_col, pd.Series(dtype=str)).str.upper().str.startswith(v.split()[0])).sum()) if fv_col in os_df_now.columns else 0
                    db_c = int((db_df_now.get(fv_col, pd.Series(dtype=str)).str.upper().str.startswith(v.split()[0])).sum()) if fv_col in db_df_now.columns else 0
                    with vcols[i]: st.metric(v, os_c+db_c, f"OS:{os_c} DB:{db_c}")

            # Guiding principles used
            principles = st.session_state.get("a5_principles", [])
            if principles:
                with st.expander(f"⚖️ {len(principles)} Guiding Principles used", expanded=False):
                    for gp in principles:
                        st.markdown(f"**{gp.get('code','?')}: {gp.get('title','?')}** — {gp.get('rule','')}")

            st.divider()
            col_chat, col_reset = st.columns(2)
            with col_chat:
                if st.button("💬 Continue conversation / refine policy", width="stretch"):
                    st.session_state.a5_status   = "chatting"
                    st.session_state.a5_os_done  = False
                    st.session_state.a5_db_done  = False
                    st.session_state.a5_ws_done  = False
                    st.session_state.a5_as_done  = False
                    st.session_state.a5_fw_done  = False
                    st.rerun()
            with col_reset:
                if st.button("🔄 Start fresh with new policy", width="stretch"):
                    PolicyAnalysisAgent.reset()
                    st.rerun()




# ── Downloads ──────────────────────────────────────────────────────────────────
st.divider()
dl_col1, dl_col2 = st.columns(2)
with dl_col1:
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
        label=f"📥 Download Excel — OS: {os_n} · DB: {db_n} entries",
        data=excel_bytes, file_name=fname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch", type="primary"
    )
    st.caption(f"📁 {fname}")

with dl_col2:
    try:
        pdf_bytes = generate_pdf_report(
            st.session_state.os_df,
            st.session_state.db_df,
            principles=st.session_state.get("a5_principles", []),
        )
        pdf_fname = f"INFY_Executive_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        st.download_button(
            label=f"📄 Download PDF Executive Report",
            data=pdf_bytes, file_name=pdf_fname,
            mime="application/pdf",
            width="stretch"
        )
        st.caption(f"📄 {pdf_fname}")
    except Exception:
        st.caption("PDF export requires fpdf2: `pip install fpdf2`")

st.markdown(
    "<p style='text-align:center;color:#94A3B8;font-size:0.72rem;margin-top:1.5rem;'>"
    "INFY Migration Reference Tracker · Infosys Enterprise Architecture · "
    "Powered by OpenAI GPT · gpt-4o-mini (A1/A2/A5) · gpt-4o-mini (A2/A5) · "
    "All data from AI knowledge base + internet verification</p>",
    unsafe_allow_html=True
)
