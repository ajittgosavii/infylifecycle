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

# Data store helpers
save_os_df      = _m_store.save_os_df
save_db_df      = _m_store.save_db_df
load_os_df      = _m_store.load_os_df
load_db_df      = _m_store.load_db_df
save_app_state  = _m_store.save_app_state
load_app_state  = _m_store.load_app_state
has_stored_data = _m_store.has_stored_data
get_rec_stats   = _m_store.get_rec_stats

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

    # Agent 1
    s1 = st.session_state.a1_status
    st.markdown(f"""<div class="agent-card a1">
    <b>🔍 Agent 1 — Internet Change Checker</b><br>{badge(s1)}
    <small style="display:block;margin-top:4px;color:#666">
    Checks internet for lifecycle date changes.<br>
    Data pre-loaded from OpenAI knowledge base<br>
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
    OpenAI fills Recommendation column for all rows</small>
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


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="infy-header">
  <h1>🖥️ INFY Migration Version Lifecycle Tracker</h1>
  <p>Infosys Enterprise Architecture &nbsp;·&nbsp;
     Powered by OpenAI GPT &nbsp;·&nbsp;
     Pre-loaded: 149 OS versions + 172 DB versions from AI knowledge base &nbsp;·&nbsp;
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
- Baseline: **{len(OS_DATA)} OS + {len(DB_DATA)} DB** rows pre-loaded from OpenAI knowledge
- Task: Checks internet for lifecycle date changes only
- Tool: `gpt-4o-mini (16 targeted checks)
- Updates: Notes column with [Web verified: date]""")

    s2 = st.session_state.a2_status
    with ca2:
        icon2 = {"idle":"⚪","running":"🔵","done":"✅","error":"❌"}.get(s2,"⚪")
        st.markdown(f"""**{icon2} Agent 2 — Recommendation Engine**
- Status: `{s2.upper()}`
- Tool: gpt-4o-mini (cost-efficient)
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
**Data is pre-loaded** — {len(OS_DATA)} OS versions and {len(DB_DATA)} DB versions are visible immediately from AI knowledge base.

1. **Enter your OpenAI API key** in the sidebar (or add `OPENAI_API_KEY` to Streamlit Cloud Secrets)
2. **Run Agent 2** — OpenAI fills expert recommendations for all {len(OS_DATA)+len(DB_DATA)} rows (recommended first step)
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
        Chat with Agent 5 → It collects your policy context → Generates Final Recommendations sheet
      </p>
    </div>""", unsafe_allow_html=True)

    if not key_ok:
        st.warning("⚠️ Enter your OpenAI API key in the sidebar to use Agent 5.")
    else:
        a5s = st.session_state.get("a5_status", "idle")

        # ── Progress stepper ──────────────────────────────────────────────────
        steps    = ["💬 Policy Chat", "⚖️ Principles", "💰 Cost Intel", "🧠 Analysis", "✅ Complete"]
        step_map = {"idle":0,"chatting":0,"principles":1,"costing":2,
                    "ready":2,"analysing":3,"done":4}
        cur_step = step_map.get(a5s, 0)
        s_cols   = st.columns(5)
        for i, (col, lbl) in enumerate(zip(s_cols, steps)):
            with col:
                if i < cur_step:
                    st.markdown(f"<div style='text-align:center;color:#10B981;font-size:0.8rem;'>✅ {lbl}</div>", unsafe_allow_html=True)
                elif i == cur_step:
                    st.markdown(f"<div style='text-align:center;color:#F59E0B;font-weight:700;font-size:0.8rem;'>● {lbl}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:center;color:#94A3B8;font-size:0.8rem;'>○ {lbl}</div>", unsafe_allow_html=True)
        st.divider()

        # ── PHASE 1: CHAT ─────────────────────────────────────────────────────
        if a5s in ("idle", "chatting"):

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

            if a5s == "idle":
                st.session_state.a5_status = "chatting"
                session_id = PolicyAnalysisAgent.get_or_create_session()
                # Save a placeholder so the welcome panel shows while opening loads
                st.session_state.a5_opening_pending = True
                st.rerun()

            session_id = PolicyAnalysisAgent.get_or_create_session()
            messages   = _load_messages(session_id)

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
                        with st.spinner("🔍 Agent 5 is searching and thinking..."):
                            agent5   = PolicyAnalysisAgent(api_key=api_key)
                            all_msgs = _load_messages(session_id)
                            reply    = agent5.chat(all_msgs)

                        done, context, summary = agent5.is_conversation_complete(reply)

                        if done:
                            complete_msg = (
                                f"✅ **I have enough policy context to proceed.**\n\n"
                                f"**Policy Summary:** {summary}\n\n"
                                f"Moving to Phase 2 — generating your Guiding Principles..."
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

            # ── Controls ──────────────────────────────────────────────────────
            if messages:
                st.divider()
                col_proceed, col_reset = st.columns([2, 1])
                with col_proceed:
                    if len(messages) >= 6:
                        if st.button("➡️ Enough context — proceed to Guiding Principles",
                                     type="primary", width="stretch"):
                            agent5     = PolicyAnalysisAgent(api_key=api_key)
                            all_msgs   = _load_messages(session_id)
                            ctx_prompt = (
                                "Extract policy context as JSON with keys: "
                                "eol_tolerance, min_runway, compliance, esu_budget, "
                                "windows_path, linux_path, db_path, oracle_stance, "
                                "cloud_provider, migration_capacity, criticality, rollback. "
                                "Return ONLY the JSON object."
                            )
                            try:
                                r = agent5.client.chat.completions.create(
                                    model="gpt-4o-mini", max_tokens=600,
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
                with st.expander("📋 Policy Context extracted from conversation", expanded=False):
                    for k, v in context.items():
                        st.markdown(f"**{k.replace('_',' ').title()}:** {v}")

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

            # OS analysis
            if not st.session_state.get("a5_os_done"):
                agent5     = PolicyAnalysisAgent(api_key=api_key)
                principles = st.session_state.a5_principles
                costs      = st.session_state.a5_costs
                context    = st.session_state.a5_context
                total_os   = len(st.session_state.os_df)
                _log("🧠", f"**Step 2/4 — Generating Final Recommendations for {total_os} OS entries...**")

                live = st.empty()
                def os5_cb(pct, msg):
                    prog_bar.progress(min(pct*0.5, 0.5), text=msg)
                    live.info(f"⏳ {msg}")

                new_os = agent5.analyse_os(st.session_state.os_df, principles, costs, context, os5_cb)
                st.session_state.os_df    = new_os
                st.session_state.a5_os_done = True
                # Persist Final Recommendations to SQLite
                save_os_df(new_os)

                if "Analysis Source" in new_os.columns:
                    ai_c = (new_os["Analysis Source"] == "OpenAI").sum()
                    rb_c = (new_os["Analysis Source"] == "Rule-based").sum()
                    _log("✅" if rb_c == 0 else "⚠️",
                         f"**OS done** — OpenAI: {ai_c} rows ✅" +
                         (f" | Rule-based fallback: {rb_c} rows" if rb_c else ""))
                st.rerun()

            # DB analysis
            if not st.session_state.get("a5_db_done"):
                agent5     = PolicyAnalysisAgent(api_key=api_key)
                principles = st.session_state.a5_principles
                costs      = st.session_state.a5_costs
                context    = st.session_state.a5_context
                total_db   = len(st.session_state.db_df)
                _log("🧠", f"**Step 3/4 — Generating Final Recommendations for {total_db} DB entries...**")

                live2 = st.empty()
                def db5_cb(pct, msg):
                    prog_bar.progress(min(0.5 + pct*0.5, 1.0), text=msg)
                    live2.info(f"⏳ {msg}")

                new_db = agent5.analyse_db(st.session_state.db_df, principles, costs, context, db5_cb)
                st.session_state.db_df    = new_db
                st.session_state.a5_db_done = True
                # Persist Final Recommendations to SQLite
                save_db_df(new_db)

                if "Analysis Source" in new_db.columns:
                    ai_c = (new_db["Analysis Source"] == "OpenAI").sum()
                    rb_c = (new_db["Analysis Source"] == "Rule-based").sum()
                    _log("✅" if rb_c == 0 else "⚠️",
                         f"**DB done** — OpenAI: {ai_c} rows ✅" +
                         (f" | Rule-based fallback: {rb_c} rows" if rb_c else ""))
                st.rerun()

            _log("🏁", "**Step 4/4 — Final Recommendations complete. New sheet added to Excel export.**")
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
                    st.rerun()
            with col_reset:
                if st.button("🔄 Start fresh with new policy", width="stretch"):
                    PolicyAnalysisAgent.reset()
                    st.rerun()


# ── Download Excel ─────────────────────────────────────────────────────────────

    if not key_ok:
        st.warning("⚠️ Enter your OpenAI API key in the sidebar to use Agent 5.")
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
            st.caption("Answer 15 questions across 5 categories to define your migration policy.")
            answers = st.session_state.a5_answers
            PQS = _m_analysis.POLICY_QUESTIONS
            with st.form("policy_form"):
                current_cat = None
                for q in PQS:
                    cat = q.get("category", "")
                    if cat != current_cat:
                        current_cat = cat
                        cat_icons = {
                            "Risk & Compliance":    "🔒",
                            "Budget & Commercial":  "💰",
                            "OS Strategy":          "🖥️",
                            "Database Strategy":    "🗄️",
                            "Execution & Capacity": "⚙️",
                        }
                        icon = cat_icons.get(cat, "📋")
                        st.markdown(f"---\n#### {icon} {cat}")
                    st.markdown(f"**{q['id'].upper()}. {q['q']}**")
                    current = answers.get(q["key"], q["opts"][0])
                    idx_val = q["opts"].index(current) if current in q["opts"] else 0
                    choice  = st.radio(q["id"], q["opts"], index=idx_val,
                                       label_visibility="collapsed", key=f"pq_{q['key']}")
                    answers[q["key"]] = choice
                    st.markdown("")
                submitted = st.form_submit_button(
                    "✅ Submit 15 Answers → Generate Guiding Principles",
                    type="primary", width="stretch")
            if submitted:
                st.session_state.a5_answers = answers
                st.session_state.a5_status  = "principles"
                st.rerun()

        elif a5s == "principles":
            st.subheader("⚖️ Phase 2 — Generating Guiding Principles...")
            with st.spinner("OpenAI is generating guiding principles..."):
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
            st.subheader("🧠 Agent 5 — Policy Analysis in Progress")

            # ── Init persistent log ───────────────────────────────────────────
            if "a5_log" not in st.session_state:
                st.session_state.a5_log = []

            def _log(icon, msg):
                """Append to persistent log — survives reruns."""
                st.session_state.a5_log.append(f"{icon} {msg}")

            # ── Show accumulated log so far ───────────────────────────────────
            log_box = st.container()
            with log_box:
                for entry in st.session_state.a5_log:
                    if entry.startswith("❌"):
                        st.error(entry)
                    elif entry.startswith("⚠️"):
                        st.warning(entry)
                    elif entry.startswith("✅"):
                        st.success(entry)
                    else:
                        st.info(entry)

            prog_bar = st.progress(0, text="Starting...")
            st.divider()

            # ── Step 1: Pre-flight API test ───────────────────────────────────
            if not st.session_state.get("a5_preflight_done"):
                _log("🔌", "**Step 1/4 — Testing OpenAI API connection...**")
                try:
                    from openai import OpenAI as _OAI
                    _client = _OAI(api_key=api_key)
                    _resp   = _client.chat.completions.create(
                        model="gpt-4o-mini",
                        max_tokens=30,
                        messages=[{"role": "user", "content": "Reply with only the word: READY"}]
                    )
                    _reply = _resp.choices[0].message.content.strip()
                    _log("✅", f"**OpenAI API connected** — `gpt-4o-mini` responded: **{_reply}**")
                    st.session_state.a5_preflight_done = True
                except Exception as _ex:
                    _log("❌", f"**OpenAI API FAILED** — `{str(_ex)}`\n\nCheck: API key valid? Quota exhausted? Visit platform.openai.com/usage")
                    # Show updated log and stop
                    with log_box:
                        st.error(st.session_state.a5_log[-1])
                    st.stop()
                st.rerun()   # rerun to show checkpoint before continuing

            # ── Step 2: OS Analysis ───────────────────────────────────────────
            if not st.session_state.get("a5_os_done"):
                agent5     = PolicyAnalysisAgent(api_key=api_key)
                principles = st.session_state.a5_principles
                costs      = st.session_state.a5_costs
                total_os   = len(st.session_state.os_df)
                _log("🧠", f"**Step 2/4 — OpenAI analysing {total_os} OS entries** (batches of 15)...")

                batch_log = st.empty()
                ai_batches = 0
                rb_batches = 0

                def os5_cb(pct, msg):
                    prog_bar.progress(min(pct * 0.5, 0.5), text=msg)
                    batch_log.info(f"⏳ {msg}")
                    if "OpenAI:" in msg:
                        # Extract counts from final summary message
                        pass

                new_os = agent5.analyse_os(
                    st.session_state.os_df, principles, costs, os5_cb)
                st.session_state.os_df    = new_os
                st.session_state.a5_os_done = True

                # Count results
                if "Analysis Source" in new_os.columns:
                    ai_c = (new_os["Analysis Source"] == "OpenAI").sum()
                    rb_c = (new_os["Analysis Source"] == "Rule-based").sum()
                    if rb_c == 0:
                        _log("✅", f"**OS Analysis complete** — OpenAI analysed all **{ai_c} OS rows** ✅")
                    elif ai_c == 0:
                        _log("⚠️", f"**OS Analysis complete** — ⚠️ OpenAI failed all batches. Rule-based used for {rb_c} rows. Check quota.")
                    else:
                        _log("⚠️", f"**OS Analysis complete** — OpenAI: {ai_c} rows ✅ | Rule-based fallback: {rb_c} rows ⚠️")
                else:
                    _log("✅", f"**OS Analysis complete** — {total_os} rows processed")

                st.rerun()   # rerun to show checkpoint before DB analysis

            # ── Step 3: DB Analysis ───────────────────────────────────────────
            if not st.session_state.get("a5_db_done"):
                agent5     = PolicyAnalysisAgent(api_key=api_key)
                principles = st.session_state.a5_principles
                costs      = st.session_state.a5_costs
                total_db   = len(st.session_state.db_df)
                _log("🧠", f"**Step 3/4 — OpenAI analysing {total_db} DB entries** (batches of 15)...")

                batch_log2 = st.empty()

                def db5_cb(pct, msg):
                    prog_bar.progress(min(0.5 + pct * 0.5, 1.0), text=msg)
                    batch_log2.info(f"⏳ {msg}")

                new_db = agent5.analyse_db(
                    st.session_state.db_df, principles, costs, db5_cb)
                st.session_state.db_df    = new_db
                st.session_state.a5_db_done = True

                if "Analysis Source" in new_db.columns:
                    ai_c = (new_db["Analysis Source"] == "OpenAI").sum()
                    rb_c = (new_db["Analysis Source"] == "Rule-based").sum()
                    if rb_c == 0:
                        _log("✅", f"**DB Analysis complete** — OpenAI analysed all **{ai_c} DB rows** ✅")
                    elif ai_c == 0:
                        _log("⚠️", f"**DB Analysis complete** — ⚠️ OpenAI failed all batches. Rule-based used for {rb_c} rows.")
                    else:
                        _log("⚠️", f"**DB Analysis complete** — OpenAI: {ai_c} rows ✅ | Rule-based fallback: {rb_c} rows ⚠️")
                else:
                    _log("✅", f"**DB Analysis complete** — {total_db} rows processed")

                st.rerun()   # rerun to show checkpoint before finishing

            # ── Step 4: Wrap up ───────────────────────────────────────────────
            _log("🏁", "**Step 4/4 — Analysis complete. Policy Recommendation + Verdict columns ready.**")
            st.session_state.a5_status         = "done"
            st.session_state.a5_preflight_done = False   # reset for next run
            st.session_state.a5_log            = []      # clear log (shown in done state)
            st.rerun()

        elif a5s == "done":
            st.success("✅ **Agent 5 complete!** Policy Recommendation + Verdict columns added to both tabs.")

            # Show AI vs rule-based breakdown
            os_df_now = st.session_state.os_df
            db_df_now = st.session_state.db_df
            if "Analysis Source" in os_df_now.columns or "Analysis Source" in db_df_now.columns:
                ai_os = (os_df_now.get("Analysis Source", pd.Series(dtype=str)) == "OpenAI").sum() if "Analysis Source" in os_df_now.columns else 0
                rb_os = (os_df_now.get("Analysis Source", pd.Series(dtype=str)) == "Rule-based").sum() if "Analysis Source" in os_df_now.columns else 0
                ai_db = (db_df_now.get("Analysis Source", pd.Series(dtype=str)) == "OpenAI").sum() if "Analysis Source" in db_df_now.columns else 0
                rb_db = (db_df_now.get("Analysis Source", pd.Series(dtype=str)) == "Rule-based").sum() if "Analysis Source" in db_df_now.columns else 0
                total_ai = ai_os + ai_db
                total_rb = rb_os + rb_db
                if total_ai > 0:
                    st.info(f"🤖 **OpenAI analysed {total_ai} rows** (OS: {ai_os}, DB: {ai_db})  "
                            f"| 📐 Rule-based fallback: {total_rb} rows (OS: {rb_os}, DB: {rb_db})")
                else:
                    st.warning(f"⚠️ **OpenAI did not respond** — all {total_rb} rows used rule-based analysis. "
                               f"Check your API key quota at platform.openai.com/usage")
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
    "Powered by OpenAI GPT · gpt-4o-mini (A1/A2/A5) · gpt-4o-mini (A2/A5) · "
    "All data from AI knowledge base + internet verification</p>",
    unsafe_allow_html=True
)
