"""
utils/config.py — Configurable project settings
Centralises project dates and thresholds used across agents.
"""
from datetime import date
import streamlit as st


DEFAULT_PROJECT_START = date(2026, 4, 1)
DEFAULT_PROJECT_END = date(2028, 6, 30)
DEFAULT_REFRESH_DAYS = 14

# Risk thresholds (days)
THRESHOLD_CRITICAL = 0
THRESHOLD_URGENT = 180
THRESHOLD_HIGH = 365
THRESHOLD_PLAN = 730


def get_project_start() -> date:
    return st.session_state.get("project_start", DEFAULT_PROJECT_START)


def get_project_end() -> date:
    return st.session_state.get("project_end", DEFAULT_PROJECT_END)


def render_project_settings():
    """Render project window configuration in the sidebar."""
    st.subheader("Project Window")
    start = st.date_input(
        "Project Start",
        value=get_project_start(),
        key="cfg_project_start",
        help="Migration project start date"
    )
    end = st.date_input(
        "Project End",
        value=get_project_end(),
        key="cfg_project_end",
        help="Migration project end date"
    )
    if start and end:
        st.session_state["project_start"] = start
        st.session_state["project_end"] = end
        days = (end - start).days
        st.caption(f"Window: {days} days ({days // 30} months)")
    return start, end
