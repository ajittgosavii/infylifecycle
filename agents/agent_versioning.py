"""
Agent 4: Version Guardian
Snapshots OS/DB/WS/AS/FW data before each refresh. Preserves recommendations on re-fetch.
"""
import pandas as pd
import streamlit as st
from datetime import datetime

MAX_VERSIONS = 10
PRESERVE_COLS = ["Recommendation", "Policy Recommendation", "Verdict"]


class VersionGuardianAgent:

    @staticmethod
    def init_session():
        if "a4_history" not in st.session_state:
            st.session_state.a4_history = []

    @staticmethod
    def snapshot(os_df: pd.DataFrame, db_df: pd.DataFrame, changes: list,
                 ws_df: pd.DataFrame = None, as_df: pd.DataFrame = None,
                 fw_df: pd.DataFrame = None) -> int:
        VersionGuardianAgent.init_session()
        history = st.session_state.a4_history
        v = len(history) + 1
        snap = {
            "version":    v,
            "label":      f"v{v} — {datetime.now().strftime('%d %b %Y %H:%M')}",
            "os_df":      os_df.copy(),
            "db_df":      db_df.copy(),
            "changes":    list(changes),
            "os_count":   len(os_df),
            "db_count":   len(db_df),
        }
        if ws_df is not None:
            snap["ws_df"] = ws_df.copy()
            snap["ws_count"] = len(ws_df)
        if as_df is not None:
            snap["as_df"] = as_df.copy()
            snap["as_count"] = len(as_df)
        if fw_df is not None:
            snap["fw_df"] = fw_df.copy()
            snap["fw_count"] = len(fw_df)
        history.append(snap)
        if len(history) > MAX_VERSIONS:
            st.session_state.a4_history = history[-MAX_VERSIONS:]
        return v

    @staticmethod
    def preserve_recommendations(new_os, old_os, new_db, old_db,
                                  new_ws=None, old_ws=None,
                                  new_as=None, old_as=None,
                                  new_fw=None, old_fw=None):
        """Copy recommendation columns from old data into new data where new rows are blank."""
        def _copy(new_df, old_df, key_cols):
            if old_df is None or old_df.empty or new_df is None or new_df.empty:
                return new_df
            new_df = new_df.copy()
            for col in PRESERVE_COLS:
                if col not in old_df.columns:
                    continue
                if col not in new_df.columns:
                    new_df[col] = ""
                old_lookup = {}
                for _, row in old_df.iterrows():
                    k = "|".join(str(row.get(c, "")) for c in key_cols)
                    old_lookup[k] = str(row.get(col, ""))
                for idx, row in new_df.iterrows():
                    k = "|".join(str(row.get(c, "")) for c in key_cols)
                    if not str(new_df.at[idx, col]).strip() and k in old_lookup:
                        new_df.at[idx, col] = old_lookup[k]
            return new_df

        new_os = _copy(new_os, old_os, ["OS Version"])
        new_db = _copy(new_db, old_db, ["Database", "Version"])
        new_ws = _copy(new_ws, old_ws, ["Web Server", "Version"])
        new_as = _copy(new_as, old_as, ["App Server", "Version"])
        new_fw = _copy(new_fw, old_fw, ["Framework", "Version"])
        return new_os, new_db, new_ws, new_as, new_fw

    @staticmethod
    def get_history():
        return st.session_state.get("a4_history", [])

    @staticmethod
    def render_history_tab():
        history = st.session_state.get("a4_history", [])
        if not history:
            st.info("No version history yet. Version snapshots are created automatically each time Agent 1 runs a refresh.")
            return
        st.metric("Total snapshots stored", len(history))
        st.caption(f"Maximum {MAX_VERSIONS} snapshots kept in session.")
        for snap in reversed(history):
            ws_c = snap.get('ws_count', 0)
            as_c = snap.get('as_count', 0)
            fw_c = snap.get('fw_count', 0)
            extra = f" · WS: {ws_c} · AS: {as_c} · FW: {fw_c}" if (ws_c + as_c + fw_c) > 0 else ""
            with st.expander(f"📸 {snap['label']}  —  OS: {snap['os_count']} · DB: {snap['db_count']}{extra} rows"):
                if snap.get("changes"):
                    st.markdown(f"**{len(snap['changes'])} changes detected:**")
                    for c in snap["changes"][:20]:
                        st.markdown(f"- {c}")
                else:
                    st.caption("No lifecycle date changes detected in this refresh.")
                cols = st.columns(2)
                with cols[0]:
                    st.caption("OS snapshot (first 10 rows)")
                    show_cols = [c for c in ["OS Version", "Mainstream/Full Support End",
                                             "Extended/LTSC Support End"] if c in snap["os_df"].columns]
                    st.dataframe(snap["os_df"][show_cols].head(10), hide_index=True, height=220)
                with cols[1]:
                    st.caption("DB snapshot (first 10 rows)")
                    show_cols = [c for c in ["Database", "Version", "Status",
                                             "Extended Support End"] if c in snap["db_df"].columns]
                    st.dataframe(snap["db_df"][show_cols].head(10), hide_index=True, height=220)
                # Show WS/AS/FW snapshots if present
                extra_dfs = []
                if "ws_df" in snap:
                    extra_dfs.append(("Web Servers", snap["ws_df"], ["Web Server", "Version", "Status"]))
                if "as_df" in snap:
                    extra_dfs.append(("App Servers", snap["as_df"], ["App Server", "Version", "Status"]))
                if "fw_df" in snap:
                    extra_dfs.append(("Frameworks", snap["fw_df"], ["Framework", "Version", "Status"]))
                if extra_dfs:
                    ecols = st.columns(len(extra_dfs))
                    for i, (label, edf, ecol_names) in enumerate(extra_dfs):
                        with ecols[i]:
                            st.caption(f"{label} snapshot (first 10)")
                            show = [c for c in ecol_names if c in edf.columns]
                            st.dataframe(edf[show].head(10), hide_index=True, height=180)
