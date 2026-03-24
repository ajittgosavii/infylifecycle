"""
utils/pdf_report.py — PDF Executive Report Generator
Creates a concise 2-3 page executive summary PDF.
Uses only standard library + minimal dependencies.
"""
import io
from datetime import datetime
import pandas as pd


def generate_pdf_report(os_df: pd.DataFrame, db_df: pd.DataFrame,
                        principles: list = None,
                        project_start: str = "1 Apr 2026",
                        project_end: str = "30 Jun 2028") -> bytes:
    """
    Generate a PDF executive summary report.
    Returns PDF as bytes.
    Uses fpdf2 library for PDF generation.
    """
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    ts = datetime.now().strftime("%d %B %Y %H:%M")

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_fill_color(0, 31, 91)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "INFY Migration Lifecycle Report", align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Executive Summary  |  Generated: {ts}  |  Project: {project_start} - {project_end}",
             align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # Overview metrics
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Portfolio Overview", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(2)

    total_os = len(os_df)
    total_db = len(db_df)

    # Risk counts
    risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "MINIMAL": 0}
    for df in [os_df, db_df]:
        if "Risk Level" in df.columns:
            for level in risk_counts:
                risk_counts[level] += int((df["Risk Level"] == level).sum())

    metrics = [
        f"Total OS Versions: {total_os}",
        f"Total DB Versions: {total_db}",
        f"Total Portfolio: {total_os + total_db}",
        "",
        f"CRITICAL Risk: {risk_counts['CRITICAL']}",
        f"HIGH Risk: {risk_counts['HIGH']}",
        f"MEDIUM Risk: {risk_counts['MEDIUM']}",
        f"LOW Risk: {risk_counts['LOW']}",
        f"MINIMAL Risk: {risk_counts['MINIMAL']}",
    ]

    for m in metrics:
        if m:
            pdf.cell(0, 6, f"  {m}", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.ln(3)

    pdf.ln(5)

    # Critical & High Risk Items
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Critical & High Risk Items Requiring Immediate Action", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.ln(2)

    urgent_items = []
    if "Risk Score" in os_df.columns:
        for _, row in os_df[os_df["Risk Score"] >= 60].iterrows():
            urgent_items.append({
                "name": str(row.get("OS Version", "")),
                "type": "OS",
                "risk": row.get("Risk Level", ""),
                "score": row.get("Risk Score", 0),
                "days": row.get("Days Until EOL", ""),
                "rec": str(row.get("Recommendation", ""))[:80]
            })
    if "Risk Score" in db_df.columns:
        for _, row in db_df[db_df["Risk Score"] >= 60].iterrows():
            urgent_items.append({
                "name": f"{row.get('Database', '')} {row.get('Version', '')}",
                "type": "DB",
                "risk": row.get("Risk Level", ""),
                "score": row.get("Risk Score", 0),
                "days": row.get("Days Until EOL", ""),
                "rec": str(row.get("Recommendation", ""))[:80]
            })

    urgent_items.sort(key=lambda x: x["score"], reverse=True)

    if urgent_items:
        # Table header
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(0, 48, 135)
        pdf.set_text_color(255, 255, 255)
        col_widths = [55, 12, 18, 14, 16, 75]
        headers = ["Name", "Type", "Risk", "Score", "Days", "Recommendation"]
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 7, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 7)

        for item in urgent_items[:25]:
            # Color code risk
            if item["risk"] == "CRITICAL":
                pdf.set_fill_color(255, 205, 210)
            elif item["risk"] == "HIGH":
                pdf.set_fill_color(255, 224, 178)
            else:
                pdf.set_fill_color(255, 255, 255)

            days_str = str(item["days"]) if item["days"] is not None else "N/A"

            vals = [item["name"][:30], item["type"], item["risk"],
                    str(item["score"]), days_str, item["rec"]]
            for w, v in zip(col_widths, vals):
                pdf.cell(w, 6, v, border=1, fill=True)
            pdf.ln()
    else:
        pdf.cell(0, 6, "  No critical or high risk items found.", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Guiding Principles
    if principles:
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Guiding Principles", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.ln(2)

        for gp in principles[:10]:
            code = gp.get("code", "")
            title = gp.get("title", "")
            rule = gp.get("rule", "")
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, f"  {code}: {title}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 4, f"    {rule[:120]}")
            pdf.ln(1)

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, f"INFY Migration Lifecycle Tracker | Infosys Enterprise Architecture | {ts}",
             align="C", new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.getvalue()
