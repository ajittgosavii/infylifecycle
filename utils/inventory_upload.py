"""
utils/inventory_upload.py — CSV Inventory Upload & Matching
Allows users to upload their actual server/database inventory and
join it against lifecycle data to show their specific risk exposure.
"""
import pandas as pd
import streamlit as st
from datetime import date


EXPECTED_OS_COLS = ["hostname", "os_version"]
EXPECTED_DB_COLS = ["hostname", "database", "version"]
OPTIONAL_COLS = ["environment", "tier", "location", "owner", "application"]


def render_upload_section():
    """Render the inventory upload UI. Returns (matched_os_df, matched_db_df) or (None, None)."""
    st.markdown("""
    <div style="background:linear-gradient(135deg,#EFF6FF,#FDF2F8);
                border:1px solid #BFDBFE;border-radius:12px;
                padding:1rem 1.4rem;margin-bottom:1rem;">
      <h3 style="margin:0 0 0.4rem;color:#1E40AF;font-size:1rem;">
        Upload Your Server/Database Inventory
      </h3>
      <p style="margin:0;color:#374151;font-size:0.85rem;">
        Upload a CSV of your actual infrastructure to see <strong>your specific</strong>
        risk exposure matched against lifecycle data.
      </p>
    </div>""", unsafe_allow_html=True)

    with st.expander("CSV Format Guide", expanded=False):
        st.markdown("""
**OS Inventory CSV columns:**
| Column | Required | Description |
|--------|----------|-------------|
| `hostname` | Yes | Server hostname |
| `os_version` | Yes | e.g. "Windows Server 2016", "RHEL 8" |
| `environment` | No | e.g. "Production", "Dev", "Staging" |
| `tier` | No | e.g. "Tier-1", "Tier-2", "Tier-3" |
| `application` | No | Application running on this server |

**DB Inventory CSV columns:**
| Column | Required | Description |
|--------|----------|-------------|
| `hostname` | Yes | Server hostname |
| `database` | Yes | e.g. "SQL Server", "Oracle" |
| `version` | Yes | e.g. "2016", "19c" |
| `environment` | No | e.g. "Production", "Dev" |
| `tier` | No | e.g. "Tier-1", "Tier-2" |
        """)

    col1, col2 = st.columns(2)
    with col1:
        os_file = st.file_uploader("OS Inventory CSV", type=["csv"], key="inv_os_upload")
    with col2:
        db_file = st.file_uploader("DB Inventory CSV", type=["csv"], key="inv_db_upload")

    matched_os = None
    matched_db = None

    if os_file:
        matched_os = _process_os_inventory(os_file)
    if db_file:
        matched_db = _process_db_inventory(db_file)

    return matched_os, matched_db


def _process_os_inventory(uploaded_file) -> pd.DataFrame:
    """Parse uploaded OS CSV and match against lifecycle data."""
    try:
        inv = pd.read_csv(uploaded_file)
        inv.columns = [c.strip().lower().replace(" ", "_") for c in inv.columns]

        if "os_version" not in inv.columns:
            st.error("OS CSV must have an 'os_version' column.")
            return None

        st.success(f"Loaded {len(inv)} OS inventory entries")
        return inv

    except Exception as e:
        st.error(f"Error reading OS CSV: {e}")
        return None


def _process_db_inventory(uploaded_file) -> pd.DataFrame:
    """Parse uploaded DB CSV and match against lifecycle data."""
    try:
        inv = pd.read_csv(uploaded_file)
        inv.columns = [c.strip().lower().replace(" ", "_") for c in inv.columns]

        if "database" not in inv.columns:
            st.error("DB CSV must have a 'database' column.")
            return None

        st.success(f"Loaded {len(inv)} DB inventory entries")
        return inv

    except Exception as e:
        st.error(f"Error reading DB CSV: {e}")
        return None


def match_os_inventory(inventory: pd.DataFrame, lifecycle_df: pd.DataFrame) -> pd.DataFrame:
    """
    Match inventory OS versions against lifecycle data.
    Returns enriched inventory with lifecycle + risk data.
    """
    results = []
    for _, inv_row in inventory.iterrows():
        inv_os = str(inv_row.get("os_version", "")).strip()
        if not inv_os:
            continue

        # Fuzzy match against lifecycle data
        best_match = None
        best_score = 0
        for _, lc_row in lifecycle_df.iterrows():
            lc_os = str(lc_row.get("OS Version", ""))
            score = _fuzzy_match_score(inv_os, lc_os)
            if score > best_score:
                best_score = score
                best_match = lc_row

        row_data = inv_row.to_dict()
        if best_match is not None and best_score >= 0.4:
            row_data["Matched OS Version"] = best_match.get("OS Version", "")
            row_data["Match Confidence"] = f"{best_score:.0%}"
            row_data["Mainstream End"] = best_match.get("Mainstream/Full Support End", "")
            row_data["Extended End"] = best_match.get("Extended/LTSC Support End", "")
            row_data["Risk Score"] = best_match.get("Risk Score", "")
            row_data["Risk Level"] = best_match.get("Risk Level", "")
            row_data["Days Until EOL"] = best_match.get("Days Until EOL", "")
            row_data["Recommendation"] = best_match.get("Recommendation", "")
            row_data["Upgrade"] = best_match.get("Upgrade", "")
            row_data["Replace"] = best_match.get("Replace", "")
            row_data["Primary Alternative"] = best_match.get("Primary Alternative", "")
        else:
            row_data["Matched OS Version"] = "No match found"
            row_data["Match Confidence"] = "0%"
            row_data["Risk Level"] = "UNKNOWN"

        results.append(row_data)

    return pd.DataFrame(results)


def match_db_inventory(inventory: pd.DataFrame, lifecycle_df: pd.DataFrame) -> pd.DataFrame:
    """Match inventory DB entries against lifecycle data."""
    results = []
    for _, inv_row in inventory.iterrows():
        inv_db = str(inv_row.get("database", "")).strip()
        inv_ver = str(inv_row.get("version", "")).strip()
        if not inv_db:
            continue

        search = f"{inv_db} {inv_ver}".strip()

        best_match = None
        best_score = 0
        for _, lc_row in lifecycle_df.iterrows():
            lc_name = f"{lc_row.get('Database', '')} {lc_row.get('Version', '')}".strip()
            score = _fuzzy_match_score(search, lc_name)
            if score > best_score:
                best_score = score
                best_match = lc_row

        row_data = inv_row.to_dict()
        if best_match is not None and best_score >= 0.35:
            row_data["Matched DB"] = f"{best_match.get('Database', '')} {best_match.get('Version', '')}"
            row_data["Match Confidence"] = f"{best_score:.0%}"
            row_data["Status"] = best_match.get("Status", "")
            row_data["Extended End"] = best_match.get("Extended Support End", "")
            row_data["Risk Score"] = best_match.get("Risk Score", "")
            row_data["Risk Level"] = best_match.get("Risk Level", "")
            row_data["Days Until EOL"] = best_match.get("Days Until EOL", "")
            row_data["Recommendation"] = best_match.get("Recommendation", "")
            row_data["Primary Alternative"] = best_match.get("Primary Alternative", "")
        else:
            row_data["Matched DB"] = "No match found"
            row_data["Match Confidence"] = "0%"
            row_data["Risk Level"] = "UNKNOWN"

        results.append(row_data)

    return pd.DataFrame(results)


def _fuzzy_match_score(query: str, target: str) -> float:
    """Simple word-overlap fuzzy matching score (0-1)."""
    q_words = set(query.lower().split())
    t_words = set(target.lower().split())
    if not q_words or not t_words:
        return 0.0
    overlap = q_words & t_words
    return len(overlap) / max(len(q_words), len(t_words))


def render_inventory_results(matched_os: pd.DataFrame, matched_db: pd.DataFrame):
    """Display matched inventory results with risk analysis."""
    if matched_os is not None and not matched_os.empty:
        st.subheader(f"OS Inventory — {len(matched_os)} servers matched")

        # Summary metrics
        if "Risk Level" in matched_os.columns:
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("Total Servers", len(matched_os))
            with mc2:
                crit = int((matched_os["Risk Level"].isin(["CRITICAL", "HIGH"])).sum())
                st.metric("Critical/High Risk", crit)
            with mc3:
                unmatched = int((matched_os["Matched OS Version"] == "No match found").sum())
                st.metric("Unmatched", unmatched)
            with mc4:
                if "environment" in matched_os.columns:
                    prod = int(matched_os["environment"].str.lower().str.contains("prod", na=False).sum())
                    st.metric("Production", prod)

        st.dataframe(matched_os, height=400, hide_index=True)

    if matched_db is not None and not matched_db.empty:
        st.subheader(f"DB Inventory — {len(matched_db)} databases matched")

        if "Risk Level" in matched_db.columns:
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("Total DBs", len(matched_db))
            with mc2:
                crit = int((matched_db["Risk Level"].isin(["CRITICAL", "HIGH"])).sum())
                st.metric("Critical/High Risk", crit)
            with mc3:
                unmatched = int((matched_db["Matched DB"] == "No match found").sum())
                st.metric("Unmatched", unmatched)
            with mc4:
                if "environment" in matched_db.columns:
                    prod = int(matched_db["environment"].str.lower().str.contains("prod", na=False).sum())
                    st.metric("Production", prod)

        st.dataframe(matched_db, height=400, hide_index=True)
