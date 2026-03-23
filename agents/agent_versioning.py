"""
Agent 4: Version Guardian
Ensures no data is ever overwritten. Before every approved refresh:
  1. Snapshots the current OS and DB DataFrames with a timestamp
  2. After Agent 1 fetches new data, appends it as a new versioned layer
  3. Maintains a full in-session history of every refresh run
  4. Provides merge/diff utilities for the Excel export to include all history sheets
  5. Exposes a history viewer for the Streamlit UI
"""

import pandas as pd
from datetime import datetime
from typing import Optional
import streamlit as st


VERSION_KEY   = "version_history"   # session_state key for the history stack
MAX_VERSIONS  = 10                  # max snapshots kept in session (memory guard)


class VersionGuardianAgent:
    """
    Manages a versioned history of OS and DB DataFrames.
    Each version is a dict:
        {
          "version":    int (1, 2, 3 ...),
          "timestamp":  datetime,
          "label":      str  e.g. "v1 — 23 Mar 2026 14:05",
          "os_df":      pd.DataFrame,
          "db_df":      pd.DataFrame,
          "os_count":   int,
          "db_count":   int,
          "changes":    list[str]   (diff vs previous version)
        }
    """

    # ── Init / session bootstrap ──────────────────────────────────────────────
    def init_session(self):
        """Call once at app startup to ensure history list exists."""
        if VERSION_KEY not in st.session_state:
            st.session_state[VERSION_KEY] = []

    # ── Core: snapshot before refresh ────────────────────────────────────────
    def snapshot_before_refresh(
        self,
        os_df: pd.DataFrame,
        db_df: pd.DataFrame,
        changes: list[str]
    ) -> int:
        """
        Called by app.py immediately BEFORE Agent 1 runs (on Approve).
        Saves the current state as a numbered version so it can never be lost.
        Returns the new version number.
        """
        self.init_session()
        history: list = st.session_state[VERSION_KEY]

        version_num = len(history) + 1
        ts = datetime.now()
        label = f"v{version_num} — {ts.strftime('%d %b %Y %H:%M')}"

        snapshot = {
            "version":   version_num,
            "timestamp": ts,
            "label":     label,
            "os_df":     os_df.copy(),
            "db_df":     db_df.copy(),
            "os_count":  len(os_df),
            "db_count":  len(db_df),
            "changes":   list(changes),
        }

        history.append(snapshot)

        # Keep only the most recent MAX_VERSIONS
        if len(history) > MAX_VERSIONS:
            history.pop(0)

        st.session_state[VERSION_KEY] = history
        return version_num

    # ── Core: record newly fetched data as latest version ────────────────────
    def record_new_version(
        self,
        os_df: pd.DataFrame,
        db_df: pd.DataFrame,
        changes: list[str]
    ) -> int:
        """
        Called AFTER Agent 1 + Agent 2 complete.
        Adds the fresh data as the newest version in history.
        Returns the new version number.
        """
        self.init_session()
        history: list = st.session_state[VERSION_KEY]

        version_num = len(history) + 1
        ts = datetime.now()
        label = f"v{version_num} — {ts.strftime('%d %b %Y %H:%M')} (latest)"

        snapshot = {
            "version":   version_num,
            "timestamp": ts,
            "label":     label,
            "os_df":     os_df.copy(),
            "db_df":     db_df.copy(),
            "os_count":  len(os_df),
            "db_count":  len(db_df),
            "changes":   list(changes),
        }

        history.append(snapshot)

        if len(history) > MAX_VERSIONS:
            history.pop(0)

        st.session_state[VERSION_KEY] = history
        return version_num

    # ── Append logic: merge old + new, no row lost ────────────────────────────
    def append_new_data(
        self,
        existing_os: pd.DataFrame,
        new_os: pd.DataFrame,
        existing_db: pd.DataFrame,
        new_db: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Merges existing data with freshly fetched data:
        - Rows that exist in both → new version wins (dates may have changed)
        - Rows only in existing  → kept as-is (version not removed by refresh)
        - Rows only in new       → appended as new entries
        Returns (merged_os_df, merged_db_df).
        """
        merged_os = _merge_frames(
            existing_os, new_os,
            key_cols=["OS Version"]
        )
        merged_db = _merge_frames(
            existing_db, new_db,
            key_cols=["Database", "Version"]
        )
        return merged_os, merged_db

    # ── Getters ───────────────────────────────────────────────────────────────
    def get_history(self) -> list:
        self.init_session()
        return st.session_state.get(VERSION_KEY, [])

    def get_version_count(self) -> int:
        return len(self.get_history())

    def get_version(self, version_num: int) -> Optional[dict]:
        for v in self.get_history():
            if v["version"] == version_num:
                return v
        return None

    def get_latest(self) -> Optional[dict]:
        h = self.get_history()
        return h[-1] if h else None

    # ── UI: sidebar status card ───────────────────────────────────────────────
    def render_status_card(self):
        """Compact sidebar card showing version count and latest snapshot."""
        self.init_session()
        history = self.get_history()

        if not history:
            st.info("No versions saved yet. Versions are created when Agent 3 approves a refresh.")
            return

        latest = history[-1]
        st.success(
            f"**{len(history)} version(s) stored**\n\n"
            f"Latest: **{latest['label']}**\n"
            f"OS: {latest['os_count']} rows · DB: {latest['db_count']} rows"
        )
        st.caption(f"Max versions kept in session: {MAX_VERSIONS}")

    # ── UI: full history viewer tab ───────────────────────────────────────────
    def render_history_viewer(self):
        """Full history viewer rendered inside a Streamlit tab."""
        self.init_session()
        history = self.get_history()

        if not history:
            st.markdown("""
            <div style="text-align:center;padding:3rem 2rem;color:var(--color-text-secondary);
                        border:2px dashed var(--color-border-tertiary);border-radius:12px;">
              <h3 style="color:var(--color-text-secondary);">No version history yet</h3>
              <p>Run Agent 1, then approve a second refresh via Agent 3.<br>
              Agent 4 will snapshot each version before data is updated.</p>
            </div>""", unsafe_allow_html=True)
            return

        # Summary metrics
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total versions", len(history))
        with c2:
            st.metric("Latest OS rows", history[-1]["os_count"])
        with c3:
            st.metric("Latest DB rows", history[-1]["db_count"])
        with c4:
            first_ts = history[0]["timestamp"].strftime("%d %b %Y")
            st.metric("Tracking since", first_ts)

        st.divider()

        # Version selector
        version_labels = [v["label"] for v in reversed(history)]
        selected_label = st.selectbox(
            "Select a version to inspect",
            options=version_labels,
            index=0,
            help="Versions are created each time Agent 3 approves a refresh"
        )

        selected = next(
            (v for v in history if v["label"] == selected_label), None
        )
        if not selected:
            return

        # Version detail
        st.subheader(f"Version detail — {selected['label']}")

        col_os, col_db = st.columns(2)
        with col_os:
            st.caption(f"OS Versions — {selected['os_count']} rows")
            st.dataframe(
                selected["os_df"],
                width="stretch",
                height=340,
                hide_index=True,
                column_config={
                    "OS Version":              st.column_config.TextColumn("OS Version",   width=200),
                    "Mainstream/Full Support End": st.column_config.TextColumn("Mainstream End", width=130),
                    "Recommendation":          st.column_config.TextColumn("Recommendation", width=300),
                }
            )
        with col_db:
            st.caption(f"DB Versions — {selected['db_count']} rows")
            st.dataframe(
                selected["db_df"],
                width="stretch",
                height=340,
                hide_index=True,
                column_config={
                    "Database":               st.column_config.TextColumn("Database", width=110),
                    "Version":                st.column_config.TextColumn("Version",  width=80),
                    "Status":                 st.column_config.TextColumn("Status",   width=110),
                    "Recommendation":         st.column_config.TextColumn("Recommendation", width=300),
                }
            )

        # Change log for this version
        if selected["changes"]:
            st.divider()
            st.subheader(f"Change log — {len(selected['changes'])} changes detected")
            for c in selected["changes"]:
                st.markdown(f"- {c}")
        else:
            st.info("No change log available for this version (first run or no prior data).")

        # Side-by-side comparison if ≥2 versions
        if len(history) >= 2:
            st.divider()
            st.subheader("Compare two versions")
            all_labels = [v["label"] for v in history]
            cc1, cc2 = st.columns(2)
            with cc1:
                va_label = st.selectbox("Version A", all_labels,
                                        index=max(0, len(all_labels)-2),
                                        key="cmp_a")
            with cc2:
                vb_label = st.selectbox("Version B", all_labels,
                                        index=len(all_labels)-1,
                                        key="cmp_b")

            va = next((v for v in history if v["label"] == va_label), None)
            vb = next((v for v in history if v["label"] == vb_label), None)

            if va and vb and va_label != vb_label:
                diff_os = _compare_frames(va["os_df"], vb["os_df"],
                                          key_cols=["OS Version"],
                                          watch_cols=["Mainstream/Full Support End",
                                                      "Extended/LTSC Support End"])
                diff_db = _compare_frames(va["db_df"], vb["db_df"],
                                          key_cols=["Database", "Version"],
                                          watch_cols=["Mainstream / Premier End",
                                                      "Extended Support End", "Status"])

                all_diffs = diff_os + diff_db
                if all_diffs:
                    st.success(f"{len(all_diffs)} difference(s) found between {va_label} and {vb_label}:")
                    for d in all_diffs:
                        st.markdown(f"- {d}")
                else:
                    st.info("No differences found between the two selected versions.")
            elif va_label == vb_label:
                st.warning("Select two different versions to compare.")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _make_key(row: pd.Series, key_cols: list) -> str:
    return " | ".join(str(row.get(c, "")) for c in key_cols)


def _merge_frames(
    existing: pd.DataFrame,
    new: pd.DataFrame,
    key_cols: list
) -> pd.DataFrame:
    """
    Smart merge: new data wins on matching keys, existing-only rows are preserved,
    net-new rows from new data are appended. Recommendation column is preserved
    from existing when new row has it blank.
    """
    if existing.empty:
        return new.copy()
    if new.empty:
        return existing.copy()

    # Build lookup from existing
    existing_map = {
        _make_key(row, key_cols): row.to_dict()
        for _, row in existing.iterrows()
    }

    merged_rows = []
    seen_keys   = set()

    for _, new_row in new.iterrows():
        key = _make_key(new_row, key_cols)
        seen_keys.add(key)
        row_dict = new_row.to_dict()

        if key in existing_map:
            old = existing_map[key]
            # Preserve Agent 2 recommendation if new fetch left it blank
            if not str(row_dict.get("Recommendation", "")).strip():
                row_dict["Recommendation"] = old.get("Recommendation", "")
            # Preserve Agent 5 policy columns — never overwrite with blank
            for col in ("Policy Recommendation", "Verdict"):
                if not str(row_dict.get(col, "")).strip():
                    row_dict[col] = old.get(col, "")

        merged_rows.append(row_dict)

    # Keep rows that are in existing but NOT in new (never discard old entries)
    for key, old_row in existing_map.items():
        if key not in seen_keys:
            merged_rows.append(old_row)

    merged_df = pd.DataFrame(merged_rows)

    # Restore original column order
    for col in existing.columns:
        if col not in merged_df.columns:
            merged_df[col] = ""
    merged_df = merged_df[existing.columns]
    return merged_df.reset_index(drop=True)


def _compare_frames(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    key_cols: list,
    watch_cols: list
) -> list:
    """Return human-readable diff strings between two DataFrames."""
    diffs = []
    if df_a is None or df_a.empty or df_b is None or df_b.empty:
        return diffs

    map_a = {_make_key(r, key_cols): r.to_dict() for _, r in df_a.iterrows()}
    map_b = {_make_key(r, key_cols): r.to_dict() for _, r in df_b.iterrows()}

    for key, row_b in map_b.items():
        if key not in map_a:
            diffs.append(f"➕ Added in B: {key}")
        else:
            row_a = map_a[key]
            for col in watch_cols:
                va = str(row_a.get(col, "")).strip()
                vb = str(row_b.get(col, "")).strip()
                if va != vb and vb not in ("", "nan"):
                    diffs.append(f"📅 {key} | {col}: '{va}' → '{vb}'")

    for key in map_a:
        if key not in map_b:
            diffs.append(f"➖ Removed in B: {key}")

    return diffs
