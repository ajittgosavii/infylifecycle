"""
utils/scenario_planner.py — What-If Scenario Planner
Lets users select items to upgrade and see before/after risk posture.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_scenario_planner(os_df: pd.DataFrame, db_df: pd.DataFrame):
    """Render the what-if scenario planner UI."""
    st.markdown("""
    <div style="background:linear-gradient(135deg,#F0FDF4,#ECFDF5);
                border:1px solid #BBF7D0;border-radius:12px;
                padding:1rem 1.4rem;margin-bottom:1rem;">
      <h3 style="margin:0 0 0.4rem;color:#166534;font-size:1rem;">
        What-If Scenario Planner
      </h3>
      <p style="margin:0;color:#374151;font-size:0.85rem;">
        Select items you plan to upgrade/migrate to see the <strong>before vs after</strong>
        impact on your risk posture.
      </p>
    </div>""", unsafe_allow_html=True)

    if "Risk Score" not in os_df.columns or "Risk Score" not in db_df.columns:
        st.warning("Run the Dashboard first to compute risk scores before using the scenario planner.")
        return

    # Build selection lists for high-risk items
    high_risk_os = os_df[os_df["Risk Score"] >= 40].copy()
    high_risk_db = db_df[db_df["Risk Score"] >= 40].copy()

    if high_risk_os.empty and high_risk_db.empty:
        st.success("All items have low risk scores. No urgent upgrades needed!")
        return

    st.subheader("Select items to upgrade/migrate")

    selected_os = []
    selected_db = []

    if not high_risk_os.empty:
        os_options = high_risk_os["OS Version"].tolist()
        selected_os = st.multiselect(
            f"OS Versions to upgrade ({len(os_options)} at-risk items)",
            os_options,
            help="Select OS versions you plan to upgrade"
        )

    if not high_risk_db.empty:
        db_options = (high_risk_db["Database"] + " " + high_risk_db["Version"]).tolist()
        selected_db = st.multiselect(
            f"DB Versions to migrate ({len(db_options)} at-risk items)",
            db_options,
            help="Select database versions you plan to migrate"
        )

    if not selected_os and not selected_db:
        st.info("Select items above to see the impact analysis.")
        return

    # Calculate before/after
    before_scores = _get_risk_counts(os_df, db_df)

    # Simulate upgrade: set risk score to 5 for selected items
    sim_os = os_df.copy()
    sim_db = db_df.copy()

    for os_ver in selected_os:
        mask = sim_os["OS Version"] == os_ver
        sim_os.loc[mask, "Risk Score"] = 5
        sim_os.loc[mask, "Risk Level"] = "MINIMAL"

    for db_item in selected_db:
        parts = db_item.rsplit(" ", 1)
        if len(parts) == 2:
            mask = (sim_db["Database"] + " " + sim_db["Version"]) == db_item
            sim_db.loc[mask, "Risk Score"] = 5
            sim_db.loc[mask, "Risk Level"] = "MINIMAL"

    after_scores = _get_risk_counts(sim_os, sim_db)

    # Display comparison
    st.divider()
    st.subheader("Impact Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Current State**")
        for level, count in before_scores.items():
            color = {"CRITICAL": "#DC2626", "HIGH": "#EA580C", "MEDIUM": "#D97706",
                     "LOW": "#65A30D", "MINIMAL": "#16A34A"}.get(level, "#6B7280")
            st.markdown(f"<span style='color:{color};font-weight:600;'>{level}: {count}</span>",
                        unsafe_allow_html=True)

    with col2:
        st.markdown("**After Upgrades**")
        for level, count in after_scores.items():
            before_c = before_scores.get(level, 0)
            delta = count - before_c
            delta_str = f" ({delta:+d})" if delta != 0 else ""
            color = {"CRITICAL": "#DC2626", "HIGH": "#EA580C", "MEDIUM": "#D97706",
                     "LOW": "#65A30D", "MINIMAL": "#16A34A"}.get(level, "#6B7280")
            st.markdown(
                f"<span style='color:{color};font-weight:600;'>{level}: {count}{delta_str}</span>",
                unsafe_allow_html=True)

    # Before/After chart
    fig = _comparison_chart(before_scores, after_scores)
    st.plotly_chart(fig, use_container_width=True)

    # Summary
    before_crit = before_scores.get("CRITICAL", 0) + before_scores.get("HIGH", 0)
    after_crit = after_scores.get("CRITICAL", 0) + after_scores.get("HIGH", 0)
    reduction = before_crit - after_crit
    total_selected = len(selected_os) + len(selected_db)

    st.markdown(f"""
    **Summary:**
    - Upgrading **{total_selected}** item(s) reduces critical/high risk items from
      **{before_crit}** to **{after_crit}** (a **{reduction}** item reduction)
    - Risk reduction: **{(reduction / max(before_crit, 1) * 100):.0f}%**
    """)


def _get_risk_counts(os_df: pd.DataFrame, db_df: pd.DataFrame) -> dict:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "MINIMAL": 0}
    for df in [os_df, db_df]:
        if "Risk Level" in df.columns:
            for level in counts:
                counts[level] += int((df["Risk Level"] == level).sum())
    return counts


def _comparison_chart(before: dict, after: dict) -> go.Figure:
    levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]
    colors_before = ["#DC2626", "#EA580C", "#D97706", "#65A30D", "#16A34A"]
    colors_after = ["#FCA5A5", "#FDBA74", "#FCD34D", "#A3E635", "#4ADE80"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Before",
        x=levels,
        y=[before.get(l, 0) for l in levels],
        marker_color=colors_before,
        text=[before.get(l, 0) for l in levels],
        textposition="auto"
    ))
    fig.add_trace(go.Bar(
        name="After Upgrade",
        x=levels,
        y=[after.get(l, 0) for l in levels],
        marker_color=colors_after,
        text=[after.get(l, 0) for l in levels],
        textposition="auto"
    ))

    fig.update_layout(
        barmode="group",
        title="Before vs After Risk Comparison",
        height=350,
        margin=dict(t=50, b=30, l=40, r=20),
        font=dict(family="Calibri, sans-serif"),
        yaxis_title="Count"
    )
    return fig
