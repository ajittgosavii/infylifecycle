"""
INFY Migration Version Tracker
Multi-Agent Streamlit Application — Infosys Enterprise Architecture

3 Agents:
  Agent 1 — Fetches/verifies OS & DB lifecycle data via Claude AI web search
  Agent 2 — Generates expert AI recommendations per OS/DB version entry
  Agent 3 — Bi-weekly refresh monitor with user permission dialog
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agents.agent_os import OSDataAgent
from agents.agent_db import RecommendationAgent
from agents.agent_refresh import RefreshAgent
from utils.excel_export import export_to_excel
from baseline_data import OS_DATA, DB_DATA

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="INFY Version Lifecycle Tracker",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "INFY Migration Reference Version Tracker — Powered by Claude AI (Anthropic)"}
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.infy-header {
    background: linear-gradient(135deg, #001F5B 0%, #003087 60%, #0057C8 100%);
    padding: 1.2rem 2rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1.5rem;
}
.infy-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
.infy-header p  { margin: 4px 0 0; font-size: 0.85rem; opacity: 0.8; }

.agent-card {
    border-left: 4px solid;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    background: rgba(0,0,0,0.03);
}
.agent-card.a1 { border-color: #0EA5E9; }
.agent-card.a2 { border-color: #8B5CF6; }
.agent-card.a3 { border-color: #F59E0B; }

.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
}
.badge-idle    { background: #F1F5F9; color: #64748B; }
.badge-running { background: #FEF3C7; color: #92400E; }
.badge-done    { background: #D1FAE5; color: #065F46; }
.badge-error   { background: #FEE2E2; color: #991B1B; }

.metric-box {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "os_df":          pd.DataFrame(OS_DATA),
        "db_df":          pd.DataFrame(DB_DATA),
        "last_refresh":   None,
        "agent1_status":  "idle",
        "agent2_status":  "idle",
        "agent3_skip":    None,
        "changes_log":    [],
        "old_os_df":      None,
        "old_db_df":      None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

refresh_agent = RefreshAgent()


# ── Helper: status badge HTML ─────────────────────────────────────────────────
def badge(status: str) -> str:
    cls_map = {"idle": "idle", "running": "running", "done": "done", "error": "error"}
    cls = cls_map.get(status.lower(), "idle")
    icons = {"idle": "◌", "running": "⟳", "done": "✓", "error": "✕"}
    return f'<span class="badge badge-{cls}">{icons.get(cls,"·")} {status.upper()}</span>'


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Infosys_logo.svg/1200px-Infosys_logo.svg.png",
             width=140)
    st.divider()

    # API Key
    st.subheader("🔑 Anthropic API Key")
    api_key = st.text_input(
        "Enter your API key", type="password",
        help="Your Anthropic API key. On Streamlit Cloud, add it to st.secrets as ANTHROPIC_API_KEY",
        placeholder="sk-ant-..."
    )
    # Try secrets if not typed
    if not api_key:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            pass

    key_ok = bool(api_key and api_key.startswith("sk-ant"))
    if api_key and not key_ok:
        st.error("⚠️ Key must start with sk-ant-")
    elif key_ok:
        st.success("✅ API key loaded")

    st.divider()

    # ── Agent 1 ────────────────────────────────────────────────────────────
    st.markdown(f"""<div class="agent-card a1">
    <b>🔍 Agent 1 — Data Fetcher</b><br>
    {badge(st.session_state.agent1_status)}
    <small style="display:block;margin-top:4px;color:#666">
    Fetches latest OS & DB lifecycle dates via Claude web search</small>
    </div>""", unsafe_allow_html=True)

    run_agent1 = st.button(
        "▶ Run Agent 1 — Fetch Data",
        disabled=not key_ok,
        use_container_width=True,
        help="Searches the web for current lifecycle dates and verifies baseline data"
    )

    st.divider()

    # ── Agent 2 ────────────────────────────────────────────────────────────
    st.markdown(f"""<div class="agent-card a2">
    <b>🤖 Agent 2 — Recommendation Engine</b><br>
    {badge(st.session_state.agent2_status)}
    <small style="display:block;margin-top:4px;color:#666">
    AI expert fills the Recommendation column for all OS & DB entries</small>
    </div>""", unsafe_allow_html=True)

    run_agent2 = st.button(
        "▶ Run Agent 2 — Generate Recommendations",
        disabled=not key_ok,
        use_container_width=True,
        help="Uses Claude AI to generate per-row expert recommendations"
    )

    st.divider()

    # ── Agent 3 ────────────────────────────────────────────────────────────
    st.markdown("""<div class="agent-card a3">
    <b>🔄 Agent 3 — Refresh Monitor</b>
    <small style="display:block;margin-top:4px;color:#666">
    Monitors 14-day refresh schedule and seeks permission to re-run</small>
    </div>""", unsafe_allow_html=True)

    refresh_agent.render_status_card(st.session_state.last_refresh)

    st.divider()

    # Summary stats
    st.caption(f"📊 OS Versions: **{len(st.session_state.os_df)}** rows")
    st.caption(f"📊 DB Versions: **{len(st.session_state.db_df)}** rows")
    os_recs = (st.session_state.os_df["Recommendation"] != "").sum()
    db_recs = (st.session_state.db_df["Recommendation"] != "").sum()
    st.caption(f"✅ Recommendations filled: OS {os_recs}/{len(st.session_state.os_df)}, DB {db_recs}/{len(st.session_state.db_df)}")


# ── Main area header ──────────────────────────────────────────────────────────
st.markdown("""
<div class="infy-header">
  <h1>🖥️ INFY Migration Version Lifecycle Tracker</h1>
  <p>Infosys Enterprise Architecture · AI-Powered OS & Database Lifecycle Intelligence · Powered by Claude AI</p>
</div>
""", unsafe_allow_html=True)


# ── Agent 3: Refresh permission banner ───────────────────────────────────────
skip_until = st.session_state.get("agent3_skip")
skip_active = skip_until and datetime.now() < skip_until

if (refresh_agent.is_refresh_due(st.session_state.last_refresh) and
        not skip_active and key_ok):
    approved = refresh_agent.render_refresh_banner(st.session_state.last_refresh)
    if approved:
        st.session_state.agent1_status = "idle"
        st.session_state.agent2_status = "idle"
        st.toast("✅ Refresh approved — re-run Agents 1 & 2 from the sidebar.")


# ── Run Agent 1 ───────────────────────────────────────────────────────────────
if run_agent1:
    st.session_state.agent1_status = "running"
    progress_bar = st.progress(0, text="Agent 1 starting web search...")
    status_text = st.empty()

    def a1_progress(pct, msg):
        progress_bar.progress(pct, text=msg)
        status_text.caption(msg)

    try:
        agent1 = OSDataAgent(api_key=api_key)
        updates = agent1.fetch_updates(progress_callback=a1_progress)

        # Save old data for change detection
        st.session_state.old_os_df = st.session_state.os_df.copy()
        st.session_state.old_db_df = st.session_state.db_df.copy()

        new_os_df, changes = agent1.merge_updates_into_df(st.session_state.os_df, updates)
        st.session_state.os_df = new_os_df
        st.session_state.changes_log = changes
        st.session_state.last_refresh = datetime.now()
        st.session_state.agent1_status = "done"

        progress_bar.progress(1.0, text="✅ Agent 1 complete!")
        if changes:
            st.success(f"Agent 1 found **{len(changes)} changes** in lifecycle data:")
            for c in changes[:10]:
                st.markdown(f"  - {c}")
        else:
            st.success("✅ Agent 1 complete — baseline data verified, no major changes detected.")

    except Exception as e:
        st.session_state.agent1_status = "error"
        st.error(f"❌ Agent 1 error: {e}")

    st.rerun()


# ── Run Agent 2 ───────────────────────────────────────────────────────────────
if run_agent2:
    st.session_state.agent2_status = "running"

    try:
        agent2 = RecommendationAgent(api_key=api_key)

        # OS recommendations
        st.info("🤖 Agent 2: Generating OS recommendations...")
        os_progress = st.progress(0, text="Processing OS versions...")

        def os_cb(pct, msg):
            os_progress.progress(pct, text=msg)

        new_os = agent2.generate_os_recommendations(st.session_state.os_df, progress_callback=os_cb)
        st.session_state.os_df = new_os

        # DB recommendations
        st.info("🤖 Agent 2: Generating DB recommendations...")
        db_progress = st.progress(0, text="Processing DB versions...")

        def db_cb(pct, msg):
            db_progress.progress(pct, text=msg)

        new_db = agent2.generate_db_recommendations(st.session_state.db_df, progress_callback=db_cb)
        st.session_state.db_df = new_db

        st.session_state.agent2_status = "done"
        if st.session_state.last_refresh is None:
            st.session_state.last_refresh = datetime.now()

        st.success("✅ Agent 2 complete — recommendations generated for all OS and DB entries!")

    except Exception as e:
        st.session_state.agent2_status = "error"
        st.error(f"❌ Agent 2 error: {e}")

    st.rerun()


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_os, tab_db, tab_status = st.tabs(["🖥️ OS Versions", "🗄️ DB Versions", "📋 Agent Status"])


# ── Tab 1: OS Versions ────────────────────────────────────────────────────────
with tab_os:
    col1, col2, col3, col4 = st.columns(4)
    os_df = st.session_state.os_df

    eol  = os_df["Mainstream/Full Support End"].apply(
        lambda x: isinstance(x, str) and any(k in x.lower() for k in ["ended", "end of"]) or
                  (isinstance(x, str) and x <= "2026-03-23" and len(x) == 10 and x[0].isdigit())
    ).sum()
    need_upgrade = (os_df.get("Upgrade", pd.Series(dtype=str)) == "Y").sum()
    need_replace = (os_df.get("Replace", pd.Series(dtype=str)) == "Y").sum()
    rec_filled   = (os_df["Recommendation"] != "").sum()

    with col1:
        st.metric("Total OS Entries", len(os_df))
    with col2:
        st.metric("⚠️ EOL / Expired", int(eol))
    with col3:
        st.metric("🔼 Upgrade Flagged", int(need_upgrade))
    with col4:
        st.metric("🔁 Replace Flagged", int(need_replace))

    # Filter controls
    with st.expander("🔍 Filter OS Data", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            os_families = ["All"] + sorted(set(
                v.split()[0] for v in os_df["OS Version"] if v
            ))
            family_filter = st.selectbox("OS Family", os_families)
        with fc2:
            upgrade_filter = st.selectbox("Upgrade Flag", ["All", "Y", "N"])
        with fc3:
            replace_filter = st.selectbox("Replace Flag", ["All", "Y", "N"])

    view_df = os_df.copy()
    if family_filter != "All":
        view_df = view_df[view_df["OS Version"].str.startswith(family_filter)]
    if upgrade_filter != "All":
        view_df = view_df[view_df.get("Upgrade", pd.Series(dtype=str)) == upgrade_filter]
    if replace_filter != "All":
        view_df = view_df[view_df.get("Replace", pd.Series(dtype=str)) == replace_filter]

    st.caption(f"Showing {len(view_df)} of {len(os_df)} rows")

    st.dataframe(
        view_df,
        use_container_width=True,
        height=500,
        column_config={
            "OS Version":                    st.column_config.TextColumn("OS Version", width=200),
            "Availability Date":             st.column_config.TextColumn("Available", width=110),
            "Security/Standard Support End": st.column_config.TextColumn("Security End", width=120),
            "Mainstream/Full Support End":   st.column_config.TextColumn("Mainstream End", width=130),
            "Extended/LTSC Support End":     st.column_config.TextColumn("Extended End", width=120),
            "Recommendation":                st.column_config.TextColumn("💡 Recommendation", width=400),
            "Notes":                         st.column_config.TextColumn("Notes", width=150),
            "Upgrade":                       st.column_config.TextColumn("⬆ Upgrade", width=80),
            "Replace":                       st.column_config.TextColumn("🔁 Replace", width=80),
            "Primary Alternative":           st.column_config.TextColumn("Primary Alt.", width=140),
            "Secondary Alternative":         st.column_config.TextColumn("Secondary Alt.", width=140),
        },
        hide_index=True,
    )


# ── Tab 2: DB Versions ────────────────────────────────────────────────────────
with tab_db:
    db_df = st.session_state.db_df
    d1, d2, d3, d4 = st.columns(4)

    eol_db  = (db_df.get("Status", pd.Series(dtype=str)).str.lower() == "end of life").sum()
    exp_db  = (db_df.get("Status", pd.Series(dtype=str)).str.lower() == "expiring soon").sum()
    sup_db  = (db_df.get("Status", pd.Series(dtype=str)).str.lower() == "supported").sum()
    rec_db  = (db_df["Recommendation"] != "").sum()

    with d1:
        st.metric("Total DB Entries", len(db_df))
    with d2:
        st.metric("🔴 End of Life", int(eol_db))
    with d3:
        st.metric("🟡 Expiring Soon", int(exp_db))
    with d4:
        st.metric("🟢 Supported", int(sup_db))

    # Filter
    with st.expander("🔍 Filter DB Data", expanded=False):
        df1, df2, df3 = st.columns(3)
        with df1:
            db_names = ["All"] + sorted(db_df["Database"].unique().tolist())
            db_filter = st.selectbox("Database", db_names)
        with df2:
            db_types = ["All"] + sorted(db_df["Type"].unique().tolist())
            type_filter = st.selectbox("Type", db_types)
        with df3:
            status_opts = ["All"] + sorted(db_df["Status"].unique().tolist())
            status_filter = st.selectbox("Status", status_opts)

    view_db = db_df.copy()
    if db_filter   != "All": view_db = view_db[view_db["Database"] == db_filter]
    if type_filter != "All": view_db = view_db[view_db["Type"]     == type_filter]
    if status_filter != "All": view_db = view_db[view_db["Status"] == status_filter]

    st.caption(f"Showing {len(view_db)} of {len(db_df)} rows")

    # Status colour helper
    def highlight_status(val):
        colors = {
            "end of life":   "background-color: #FFCDD2; color: #B71C1C;",
            "expiring soon": "background-color: #FFE0B2; color: #E65100;",
            "supported":     "background-color: #C8E6C9; color: #1B5E20;",
            "future":        "background-color: #E3F2FD; color: #0D47A1;",
        }
        return colors.get(str(val).lower(), "")

    styled = view_db.style.applymap(highlight_status, subset=["Status"])

    st.dataframe(
        styled,
        use_container_width=True,
        height=500,
        column_config={
            "Database":               st.column_config.TextColumn("Database", width=110),
            "Version":                st.column_config.TextColumn("Version",  width=90),
            "Type":                   st.column_config.TextColumn("Type",     width=140),
            "Mainstream / Premier End": st.column_config.TextColumn("Mainstream End", width=130),
            "Extended Support End":   st.column_config.TextColumn("Extended End", width=120),
            "Status":                 st.column_config.TextColumn("Status",  width=120),
            "Recommendation":         st.column_config.TextColumn("💡 Recommendation", width=420),
            "Notes":                  st.column_config.TextColumn("Notes",   width=200),
            "Upgrade":                st.column_config.TextColumn("⬆ Upgrade", width=80),
            "Replace":                st.column_config.TextColumn("🔁 Replace", width=80),
            "Primary Alternative":    st.column_config.TextColumn("Primary Alt.", width=140),
            "Secondary Alternative":  st.column_config.TextColumn("Secondary Alt.", width=140),
        },
        hide_index=True,
    )


# ── Tab 3: Agent Status ───────────────────────────────────────────────────────
with tab_status:
    st.subheader("🤖 Agent Activity Dashboard")

    ac1, ac2, ac3 = st.columns(3)

    with ac1:
        s1 = st.session_state.agent1_status
        icon = "🔵" if s1 == "running" else ("✅" if s1 == "done" else ("❌" if s1 == "error" else "⚪"))
        st.markdown(f"""
        **{icon} Agent 1 — Data Fetcher**
        - Status: `{s1.upper()}`
        - Task: Web search for OS & DB lifecycle dates
        - Tool: Claude AI + web_search
        - Output: Verified/updated baseline data
        """)

    with ac2:
        s2 = st.session_state.agent2_status
        icon = "🔵" if s2 == "running" else ("✅" if s2 == "done" else ("❌" if s2 == "error" else "⚪"))
        st.markdown(f"""
        **{icon} Agent 2 — Recommendation Engine**
        - Status: `{s2.upper()}`
        - Task: Generate expert recommendations
        - Tool: Claude AI (claude-opus-4-20250514)
        - Output: Filled Recommendation column
        """)

    with ac3:
        last_r = st.session_state.last_refresh
        days_left = refresh_agent.days_until_refresh(last_r)
        due = refresh_agent.is_refresh_due(last_r)
        icon = "🟡" if due else "✅"
        st.markdown(f"""
        **{icon} Agent 3 — Refresh Monitor**
        - Status: `{"REFRESH DUE" if due else "MONITORING"}`
        - Interval: Every 14 days
        - Last refresh: {last_r.strftime('%d %b %Y %H:%M') if last_r else 'Never'}
        - Next refresh: {f"In {days_left} days" if last_r else "After first run"}
        """)

    # Changes log
    if st.session_state.changes_log:
        st.divider()
        st.subheader("📋 Data Change Log (Last Agent 1 Run)")
        for c in st.session_state.changes_log:
            st.markdown(f"- {c}")
    else:
        st.info("No data changes detected yet. Run Agent 1 to begin change tracking.")

    # Instructions
    st.divider()
    st.subheader("📖 How to Use")
    st.markdown("""
    1. **Enter your Anthropic API key** in the sidebar (or set it in Streamlit Cloud secrets)
    2. **Run Agent 1** to fetch and verify the latest OS/DB lifecycle dates from the web
    3. **Run Agent 2** to have Claude AI generate expert recommendations for every row
    4. **Download Excel** below to export both sheets with recommendations
    5. **Agent 3** will automatically prompt you every 14 days to refresh the data
    
    **Streamlit Cloud Deployment:**
    - Go to your app settings → Secrets
    - Add: `ANTHROPIC_API_KEY = "sk-ant-your-key-here"`
    """)


# ── Download Excel button ─────────────────────────────────────────────────────
st.divider()
col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])

with col_dl2:
    ts_str = datetime.now().strftime("%d %b %Y %H:%M UTC")
    excel_bytes = export_to_excel(
        st.session_state.os_df,
        st.session_state.db_df,
        generated_at=ts_str
    )
    filename = f"INFY_Version_Tracker_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    st.download_button(
        label="📥 Download Excel — OS Versions + DB Versions",
        data=excel_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary",
        help="Downloads a formatted Excel file with OS Versions, DB Versions, and Summary sheets"
    )
    st.caption(f"📁 {filename} · OS: {len(st.session_state.os_df)} rows · DB: {len(st.session_state.db_df)} rows")

st.markdown(
    "<p style='text-align:center;color:#94A3B8;font-size:0.75rem;margin-top:1rem;'>"
    "INFY Migration Reference Tracker · Infosys Enterprise Architecture · "
    "Powered by Claude AI (Anthropic) · claude-opus-4-20250514</p>",
    unsafe_allow_html=True
)
