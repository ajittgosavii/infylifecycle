"""
utils/dashboard.py — Executive Dashboard with Plotly charts
Provides visual risk analysis, EOL timeline, and summary metrics.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime


def _parse_date(s):
    if not s or not isinstance(s, str):
        return None
    s = s.strip()[:10]
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def risk_distribution_chart(os_df: pd.DataFrame, db_df: pd.DataFrame) -> go.Figure:
    """Donut chart showing risk level distribution across OS + DB."""
    levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]
    colors = ["#DC2626", "#EA580C", "#D97706", "#65A30D", "#16A34A"]

    counts = []
    for level in levels:
        c = 0
        if "Risk Level" in os_df.columns:
            c += int((os_df["Risk Level"] == level).sum())
        if "Risk Level" in db_df.columns:
            c += int((db_df["Risk Level"] == level).sum())
        counts.append(c)

    fig = go.Figure(data=[go.Pie(
        labels=levels, values=counts,
        hole=0.55, marker_colors=colors,
        textinfo="label+value",
        textfont_size=12,
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
    )])
    fig.update_layout(
        title=dict(text="Risk Distribution", font=dict(size=16)),
        height=350, margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        font=dict(family="Calibri, sans-serif")
    )
    return fig


def status_breakdown_chart(os_df: pd.DataFrame, db_df: pd.DataFrame) -> go.Figure:
    """Side-by-side bar chart showing OS vs DB status breakdown."""
    # OS: count by risk level
    os_data = {"Category": "OS"}
    db_data = {"Category": "DB"}

    if "Risk Level" in os_df.columns:
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]:
            os_data[level] = int((os_df["Risk Level"] == level).sum())
    else:
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]:
            os_data[level] = 0

    if "Risk Level" in db_df.columns:
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]:
            db_data[level] = int((db_df["Risk Level"] == level).sum())
    else:
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]:
            db_data[level] = 0

    levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]
    colors = ["#DC2626", "#EA580C", "#D97706", "#65A30D", "#16A34A"]

    fig = go.Figure()
    for level, color in zip(levels, colors):
        fig.add_trace(go.Bar(
            name=level,
            x=["OS", "DB"],
            y=[os_data[level], db_data[level]],
            marker_color=color,
            text=[os_data[level], db_data[level]],
            textposition="auto"
        ))

    fig.update_layout(
        barmode="stack",
        title=dict(text="OS vs DB Risk Breakdown", font=dict(size=16)),
        height=350, margin=dict(t=50, b=20, l=40, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        font=dict(family="Calibri, sans-serif"),
        yaxis_title="Count"
    )
    return fig


def eol_timeline_chart(os_df: pd.DataFrame, db_df: pd.DataFrame,
                       project_start: date = None,
                       project_end: date = None) -> go.Figure:
    """Gantt-style timeline showing upcoming EOL dates against project window."""
    from utils.config import DEFAULT_PROJECT_START, DEFAULT_PROJECT_END
    if project_start is None:
        project_start = DEFAULT_PROJECT_START
    if project_end is None:
        project_end = DEFAULT_PROJECT_END

    today = date.today()
    items = []

    # Collect OS items with EOL in next 3 years
    for _, row in os_df.iterrows():
        end_str = str(row.get("Extended/LTSC Support End", "") or
                      row.get("Mainstream/Full Support End", ""))
        end_dt = _parse_date(end_str)
        if end_dt and today <= end_dt <= date(today.year + 3, 12, 31):
            risk = row.get("Risk Level", "MEDIUM") if "Risk Level" in os_df.columns else "MEDIUM"
            items.append({
                "Name": str(row.get("OS Version", ""))[:40],
                "EOL Date": end_dt,
                "Category": "OS",
                "Risk": risk
            })

    # Collect DB items
    for _, row in db_df.iterrows():
        end_str = str(row.get("Extended Support End", "") or
                      row.get("Mainstream / Premier End", ""))
        end_dt = _parse_date(end_str)
        if end_dt and today <= end_dt <= date(today.year + 3, 12, 31):
            risk = row.get("Risk Level", "MEDIUM") if "Risk Level" in db_df.columns else "MEDIUM"
            items.append({
                "Name": f"{row.get('Database', '')} {row.get('Version', '')}".strip()[:40],
                "EOL Date": end_dt,
                "Category": "DB",
                "Risk": risk
            })

    if not items:
        fig = go.Figure()
        fig.update_layout(
            title="No upcoming EOL dates in the next 3 years",
            height=200
        )
        return fig

    df = pd.DataFrame(items).sort_values("EOL Date")
    # Limit to top 30 most urgent
    df = df.head(30)

    color_map = {"CRITICAL": "#DC2626", "HIGH": "#EA580C", "MEDIUM": "#D97706",
                 "LOW": "#65A30D", "MINIMAL": "#16A34A"}

    fig = px.scatter(
        df, x="EOL Date", y="Name", color="Risk",
        color_discrete_map=color_map,
        symbol="Category",
        symbol_map={"OS": "circle", "DB": "diamond"},
        hover_data=["Category", "Risk", "EOL Date"],
        title="Upcoming EOL Timeline vs Project Window"
    )

    # Add project window shading
    fig.add_vrect(
        x0=project_start.isoformat(), x1=project_end.isoformat(),
        fillcolor="#3B82F6", opacity=0.08,
        line_width=2, line_color="#3B82F6", line_dash="dash",
        annotation_text="Project Window", annotation_position="top left"
    )

    # Add today line
    fig.add_vline(
        x=today.isoformat(), line_dash="dot", line_color="#6B7280",
        annotation_text="Today", annotation_position="top right"
    )

    fig.update_layout(
        height=max(400, len(df) * 22),
        margin=dict(t=60, b=30, l=200, r=30),
        font=dict(family="Calibri, sans-serif", size=11),
        yaxis=dict(autorange="reversed"),
        xaxis_title="Date",
        yaxis_title=""
    )
    return fig


def top_urgent_items(os_df: pd.DataFrame, db_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top N most urgent items (highest risk score) across OS + DB."""
    items = []

    for _, row in os_df.iterrows():
        if "Risk Score" in os_df.columns:
            items.append({
                "Name": row.get("OS Version", ""),
                "Category": "OS",
                "Risk Score": row.get("Risk Score", 0),
                "Risk Level": row.get("Risk Level", ""),
                "Days Until EOL": row.get("Days Until EOL", ""),
                "Recommendation": str(row.get("Recommendation", ""))[:100],
            })

    for _, row in db_df.iterrows():
        if "Risk Score" in db_df.columns:
            items.append({
                "Name": f"{row.get('Database', '')} {row.get('Version', '')}",
                "Category": "DB",
                "Risk Score": row.get("Risk Score", 0),
                "Risk Level": row.get("Risk Level", ""),
                "Days Until EOL": row.get("Days Until EOL", ""),
                "Recommendation": str(row.get("Recommendation", ""))[:100],
            })

    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items).sort_values("Risk Score", ascending=False).head(n)
    return df


def risk_score_histogram(os_df: pd.DataFrame, db_df: pd.DataFrame) -> go.Figure:
    """Histogram of risk scores."""
    scores = []
    cats = []
    if "Risk Score" in os_df.columns:
        scores.extend(os_df["Risk Score"].tolist())
        cats.extend(["OS"] * len(os_df))
    if "Risk Score" in db_df.columns:
        scores.extend(db_df["Risk Score"].tolist())
        cats.extend(["DB"] * len(db_df))

    if not scores:
        fig = go.Figure()
        fig.update_layout(title="No risk scores available", height=200)
        return fig

    df = pd.DataFrame({"Risk Score": scores, "Category": cats})
    fig = px.histogram(
        df, x="Risk Score", color="Category",
        nbins=20, barmode="overlay",
        color_discrete_map={"OS": "#3B82F6", "DB": "#8B5CF6"},
        title="Risk Score Distribution"
    )
    fig.update_layout(
        height=300, margin=dict(t=50, b=30, l=40, r=20),
        font=dict(family="Calibri, sans-serif"),
        xaxis_title="Risk Score (0-100)",
        yaxis_title="Count"
    )
    return fig
