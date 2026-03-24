"""
utils/risk_scoring.py — Risk Score Calculator
Computes a 1-100 risk score per OS/DB row based on EOL proximity,
upgrade/replace flags, and project window overlap.
"""
import pandas as pd
from datetime import datetime, date

DEFAULT_PROJECT_START = date(2026, 4, 1)
DEFAULT_PROJECT_END = date(2028, 6, 30)


def _parse_date(s):
    if not s or not isinstance(s, str) or s.strip() == "":
        return None
    s = s.strip()[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    if "ended" in s.lower() or "end of" in s.lower():
        return date(2000, 1, 1)  # sentinel for already-EOL
    return None


def compute_risk_score(row: dict, kind: str = "OS",
                       project_end: date = None,
                       today: date = None) -> int:
    """
    Returns a risk score from 0 (no risk) to 100 (critical).

    Factors:
    - EOL proximity relative to project end (60% weight)
    - Upgrade/Replace flags (15% weight)
    - Whether support ends during project window (15% weight)
    - Whether recommendation exists (10% weight)
    """
    if project_end is None:
        project_end = DEFAULT_PROJECT_END
    if today is None:
        today = date.today()

    score = 0.0

    # Get the latest support end date
    if kind == "OS":
        end_str = (row.get("Extended/LTSC Support End", "") or
                   row.get("Mainstream/Full Support End", ""))
    else:
        end_str = (row.get("Extended Support End", "") or
                   row.get("Mainstream / Premier End", ""))

    end_dt = _parse_date(str(end_str))

    # Factor 1: EOL proximity (60 points max)
    if end_dt:
        if end_dt < today:
            score += 60  # Already EOL — maximum risk
        else:
            days_until_eol = (end_dt - today).days
            if days_until_eol <= 0:
                score += 60
            elif days_until_eol <= 180:
                score += 55
            elif days_until_eol <= 365:
                score += 45
            elif days_until_eol <= 730:
                score += 30
            elif days_until_eol <= 1095:
                score += 15
            else:
                score += 5
    else:
        score += 20  # Unknown date = moderate risk

    # Factor 2: Upgrade/Replace flags (15 points max)
    upgrade = str(row.get("Upgrade", "N")).upper()
    replace = str(row.get("Replace", "N")).upper()
    if replace == "Y":
        score += 15
    elif upgrade == "Y":
        score += 10

    # Factor 3: Ends during project window (15 points)
    if end_dt:
        project_start = DEFAULT_PROJECT_START
        if project_start <= end_dt <= project_end:
            score += 15  # Expires during project — high impact

    # Factor 4: No recommendation yet (10 points)
    rec = str(row.get("Recommendation", "")).strip()
    if not rec:
        score += 10

    # Status-based bonus for DB
    if kind == "DB":
        status = str(row.get("Status", "")).lower()
        if status == "end of life":
            score = max(score, 85)
        elif status == "expiring soon":
            score = max(score, 60)

    return min(int(score), 100)


def compute_risk_label(score: int) -> str:
    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    elif score >= 20:
        return "LOW"
    return "MINIMAL"


def compute_risk_color(score: int) -> str:
    if score >= 80:
        return "#DC2626"
    elif score >= 60:
        return "#EA580C"
    elif score >= 40:
        return "#D97706"
    elif score >= 20:
        return "#65A30D"
    return "#16A34A"


def add_risk_scores(df: pd.DataFrame, kind: str = "OS",
                    project_end: date = None) -> pd.DataFrame:
    """Add Risk Score, Risk Level, and Days Until EOL columns to a dataframe."""
    df = df.copy()
    today = date.today()
    if project_end is None:
        project_end = DEFAULT_PROJECT_END

    scores = []
    labels = []
    colors = []
    days_list = []

    for _, row in df.iterrows():
        s = compute_risk_score(row.to_dict(), kind, project_end, today)
        scores.append(s)
        labels.append(compute_risk_label(s))
        colors.append(compute_risk_color(s))

        # Days until EOL
        if kind == "OS":
            end_str = (row.get("Extended/LTSC Support End", "") or
                       row.get("Mainstream/Full Support End", ""))
        else:
            end_str = (row.get("Extended Support End", "") or
                       row.get("Mainstream / Premier End", ""))

        end_dt = _parse_date(str(end_str))
        if end_dt:
            days = (end_dt - today).days
            days_list.append(days)
        else:
            days_list.append(None)

    df["Risk Score"] = scores
    df["Risk Level"] = labels
    df["Risk Color"] = colors
    df["Days Until EOL"] = days_list

    return df


def get_risk_summary(os_df: pd.DataFrame, db_df: pd.DataFrame) -> dict:
    """Return summary counts by risk level."""
    summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "MINIMAL": 0}
    for df in [os_df, db_df]:
        if "Risk Level" in df.columns:
            for level in summary:
                summary[level] += int((df["Risk Level"] == level).sum())
    return summary
