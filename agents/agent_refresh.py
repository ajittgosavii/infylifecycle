"""
Agent 3: Bi-Weekly Refresh Monitor
Tracks last-refresh timestamp and seeks user permission every 14 days
before triggering a new Agent 1 + Agent 2 run.
"""

from datetime import datetime, timedelta
from typing import Optional
import streamlit as st

REFRESH_INTERVAL_DAYS = 14


class RefreshAgent:
    def __init__(self):
        self.interval = timedelta(days=REFRESH_INTERVAL_DAYS)

    def is_refresh_due(self, last_refresh: Optional[datetime]) -> bool:
        """True if ≥14 days since last refresh (never triggers on first load)."""
        if last_refresh is None:
            return False
        return (datetime.now() - last_refresh) >= self.interval

    def days_until_refresh(self, last_refresh: Optional[datetime]) -> int:
        if last_refresh is None:
            return 0
        return max(0, (last_refresh + self.interval - datetime.now()).days)

    def days_since_refresh(self, last_refresh: Optional[datetime]) -> int:
        if last_refresh is None:
            return -1
        return (datetime.now() - last_refresh).days

    def render_refresh_banner(self, last_refresh: datetime,
                               os_count: int, db_count: int,
                               ws_count: int = 0, as_count: int = 0,
                               fw_count: int = 0) -> bool:
        """Renders the permission banner. Returns True if user approves."""
        days_ago = self.days_since_refresh(last_refresh)
        last_str = last_refresh.strftime("%d %b %Y at %H:%M")
        total = os_count + db_count + ws_count + as_count + fw_count

        st.warning(
            f"**🔄 Agent 3 — Scheduled Refresh Due**\n\n"
            f"Data was last refreshed **{days_ago} day(s) ago** (on {last_str}).\n"
            f"Refresh interval: **every {REFRESH_INTERVAL_DAYS} days**.\n\n"
            f"Current dataset: **{total} entries** "
            f"(OS: {os_count} · DB: {db_count} · WS: {ws_count} · AS: {as_count} · FW: {fw_count}).\n\n"
            f"Approving will re-run **Agent 1** (full web fetch of all versions) "
            f"and **Agent 2** (regenerate all recommendations). Estimated time: 4–6 minutes.",
            icon="⏰"
        )

        col_yes, col_skip, _ = st.columns([1, 1, 3])
        approved  = col_yes.button("✅ Approve Refresh",  type="primary", key="a3_approve")
        dismissed = col_skip.button("⏭️ Skip (remind in 3 days)",         key="a3_skip")

        if dismissed:
            st.session_state["a3_skip_until"] = datetime.now() + timedelta(days=3)
            st.rerun()

        return approved

    def render_status_card(self, last_refresh: Optional[datetime],
                            os_count: int = 0, db_count: int = 0,
                            ws_count: int = 0, as_count: int = 0,
                            fw_count: int = 0):
        """Sidebar status widget for Agent 3."""
        if last_refresh is None:
            st.info("🕐 No refresh yet. Run Agent 1 to start tracking.")
            return

        days_ago  = self.days_since_refresh(last_refresh)
        days_left = self.days_until_refresh(last_refresh)
        last_str  = last_refresh.strftime("%d %b %Y %H:%M")

        if self.is_refresh_due(last_refresh):
            st.error(f"⚠️ Refresh overdue! Last: {last_str} ({days_ago}d ago)")
        elif days_left <= 3:
            st.warning(f"⏰ Refresh due in {days_left}d. Last: {last_str}")
        else:
            st.success(f"✅ Next refresh in {days_left}d. Last: {last_str}")

        total = os_count + db_count + ws_count + as_count + fw_count
        st.caption(f"📊 {total} entries · OS:{os_count} DB:{db_count} WS:{ws_count} AS:{as_count} FW:{fw_count}")
