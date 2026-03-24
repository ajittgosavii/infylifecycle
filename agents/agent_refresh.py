"""
Agent 3: Bi-Weekly Refresh Monitor
Tracks when data was last refreshed and seeks user permission to trigger a refresh
if 14 days have elapsed. Detects changes between old and new data.
"""
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from typing import Optional


REFRESH_INTERVAL_DAYS = 14


class RefreshAgent:
    def __init__(self):
        self.interval = timedelta(days=REFRESH_INTERVAL_DAYS)

    def is_refresh_due(self, last_refresh: Optional[datetime]) -> bool:
        """Returns True if 14+ days have passed since last refresh, or never refreshed."""
        if last_refresh is None:
            return False  # Don't prompt on first load; user must run agents manually first
        return (datetime.now() - last_refresh) >= self.interval

    def days_until_refresh(self, last_refresh: Optional[datetime]) -> int:
        """Returns number of days until next scheduled refresh."""
        if last_refresh is None:
            return 0
        next_refresh = last_refresh + self.interval
        delta = (next_refresh - datetime.now()).days
        return max(0, delta)

    def days_since_refresh(self, last_refresh: Optional[datetime]) -> int:
        """Returns how many days ago the last refresh occurred."""
        if last_refresh is None:
            return -1
        return (datetime.now() - last_refresh).days

    def detect_changes(self, old_df: pd.DataFrame, new_df: pd.DataFrame,
                       key_col: str, check_cols: list) -> list:
        """
        Compare old and new dataframes and return list of detected changes.
        Returns list of change description strings.
        """
        changes = []
        if old_df is None or old_df.empty:
            return changes

        for _, new_row in new_df.iterrows():
            key = new_row[key_col]
            old_matches = old_df[old_df[key_col] == key]

            if old_matches.empty:
                changes.append(f"➕ NEW ENTRY: {key} added to dataset")
                continue

            old_row = old_matches.iloc[0]
            for col in check_cols:
                if col not in new_row or col not in old_row:
                    continue
                old_val = str(old_row[col]).strip()
                new_val = str(new_row[col]).strip()
                if old_val != new_val and new_val not in ("", "nan"):
                    changes.append(
                        f"📅 CHANGE: {key} | {col}: '{old_val}' → '{new_val}'"
                    )

        # Check for removed entries
        for _, old_row in old_df.iterrows():
            key = old_row[key_col]
            if key not in new_df[key_col].values:
                changes.append(f"➖ REMOVED: {key} no longer in dataset")

        return changes

    def render_refresh_banner(self, last_refresh: datetime) -> bool:
        """
        Renders the refresh permission banner in Streamlit.
        Returns True if user approves the refresh.
        """
        days_ago = self.days_since_refresh(last_refresh)
        last_str = last_refresh.strftime("%d %b %Y %H:%M") if last_refresh else "Never"

        st.warning(
            f"🔄 **Agent 3 — Refresh Due**\n\n"
            f"Data was last refreshed **{days_ago} days ago** (on {last_str}). "
            f"Scheduled refresh interval is **every {REFRESH_INTERVAL_DAYS} days**.\n\n"
            f"Agent 3 has detected that updated lifecycle data may be available. "
            f"Running a refresh will re-trigger **Agent 1** (web data fetch) and "
            f"**Agent 2** (recommendation update). This may take 1–2 minutes.",
            icon="⏰"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            approved = st.button("✅ Approve Refresh", type="primary", key="agent3_approve")
        with col2:
            dismissed = st.button("⏭️ Skip This Time", key="agent3_skip")

        if dismissed:
            st.session_state["agent3_skip_until"] = datetime.now() + timedelta(days=3)
            st.rerun()

        return approved

    def render_status_card(self, last_refresh: Optional[datetime]):
        """Renders Agent 3 status in the sidebar."""
        if last_refresh is None:
            st.info("🕐 No refresh recorded yet. Run Agents 1 & 2 to start tracking.")
            return

        days_ago = self.days_since_refresh(last_refresh)
        days_left = self.days_until_refresh(last_refresh)
        last_str = last_refresh.strftime("%d %b %Y at %H:%M")

        if self.is_refresh_due(last_refresh):
            st.error(f"⚠️ Refresh overdue! Last run: {last_str} ({days_ago}d ago)")
        elif days_left <= 3:
            st.warning(f"⏰ Refresh in {days_left} days. Last run: {last_str}")
        else:
            st.success(f"✅ Next refresh in {days_left} days. Last: {last_str}")
