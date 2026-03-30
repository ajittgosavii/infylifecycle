"""
utils/pdf_report.py — Professional PDF Executive Report Generator
Comprehensive multi-page report with executive summary, risk analysis,
guiding principles, cost analysis, migration waves, and compliance.
"""
import io
from datetime import datetime
import pandas as pd


def _safe(text):
    """Sanitize text for fpdf — replace Unicode chars that Helvetica can't render."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return (text.replace("→", "->").replace("←", "<-").replace("↑", "^").replace("↓", "v")
                .replace("·", "-").replace("—", "-").replace("–", "-")
                .replace("✅", "[OK]").replace("❌", "[X]").replace("⚠️", "[!]")
                .replace("🔴", "*").replace("🟠", "*").replace("🟡", "*").replace("🟢", "*")
                .replace("📋", "").replace("🧠", "").replace("💰", "").replace("📊", "")
                .replace("🖥️", "").replace("🗄️", "").replace("📦", "").replace("🌐", "")
                .replace("⚙️", "").replace("☁️", "").replace("🔁", "").replace("⬆️", "")
                .replace("\u2019", "'").replace("\u2018", "'")
                .replace("\u201c", '"').replace("\u201d", '"')
                .encode("latin-1", errors="replace").decode("latin-1"))


def generate_pdf_report(os_df: pd.DataFrame, db_df: pd.DataFrame,
                        principles: list = None,
                        costs: dict = None,
                        gp_table: list = None,
                        costed_data: list = None,
                        project_start: str = "1 Apr 2026",
                        project_end: str = "30 Jun 2028") -> bytes:
    from fpdf import FPDF

    class PDF(FPDF):
        def header(self):
            if self.page_no() > 1:
                self.set_font("Helvetica", "I", 7)
                self.set_text_color(128, 128, 128)
                self.cell(0, 5, "INFY Migration Lifecycle Report | Infosys Enterprise Architecture | CONFIDENTIAL",
                         align="L")
                self.cell(0, 5, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
                self.line(10, 12, 200, 12)
                self.ln(3)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(128, 128, 128)
            self.cell(0, 5, f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')} | Page {self.page_no()}",
                     align="C")

        def section_header(self, title, color=(0, 31, 91)):
            self.set_font("Helvetica", "B", 14)
            self.set_fill_color(*color)
            self.set_text_color(255, 255, 255)
            self.cell(0, 9, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(0, 0, 0)
            self.ln(4)

        def kpi_row(self, items):
            w = 190 / len(items)
            self.set_font("Helvetica", "B", 16)
            for label, value in items:
                self.cell(w, 10, str(value), align="C")
            self.ln()
            self.set_font("Helvetica", "", 7)
            self.set_text_color(100, 100, 100)
            for label, value in items:
                self.cell(w, 5, label, align="C")
            self.set_text_color(0, 0, 0)
            self.ln(6)

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    ts = datetime.now().strftime("%d %B %Y")
    total_os = len(os_df)
    total_db = len(db_df)

    # ── PAGE 1: COVER ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(0, 31, 91)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(255, 255, 255)
    pdf.ln(60)
    pdf.cell(0, 15, "INFY Migration", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 15, "Lifecycle Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(147, 197, 253)
    pdf.cell(0, 8, "Executive Summary & Migration Strategy", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(191, 219, 254)
    pdf.cell(0, 7, f"Project Window: {project_start} - {project_end}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Report Date: {ts}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Portfolio: {total_os} OS + {total_db} DB = {total_os+total_db} technologies", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(40)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(110, 231, 183)
    pdf.cell(0, 6, "Infosys Enterprise Architecture | Powered by AI (OpenAI GPT)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "5 AI Agents: Sentinel - Advisor - Watchdog - Guardian - Strategist", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "CONFIDENTIAL", align="C", new_x="LMARGIN", new_y="NEXT")

    # ── PAGE 2: EXECUTIVE SUMMARY ────────────────────────────────────────────
    pdf.add_page()
    pdf.section_header("1. Executive Summary")

    # Risk counts
    risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "MINIMAL": 0}
    for df in [os_df, db_df]:
        if "Risk Level" in df.columns:
            for level in risk_counts:
                risk_counts[level] += int((df["Risk Level"] == level).sum())

    pdf.kpi_row([
        ("Total Portfolio", total_os + total_db),
        ("Critical", risk_counts["CRITICAL"]),
        ("High", risk_counts["HIGH"]),
        ("Medium", risk_counts["MEDIUM"]),
        ("Low", risk_counts["LOW"]),
        ("Minimal", risk_counts["MINIMAL"]),
    ])

    # Recommendations count
    os_recs = int((os_df["Recommendation"] != "").sum()) if "Recommendation" in os_df.columns else 0
    db_recs = int((db_df["Recommendation"] != "").sum()) if "Recommendation" in db_df.columns else 0
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"AI Recommendations Generated: OS {os_recs}/{total_os} · DB {db_recs}/{total_db}", new_x="LMARGIN", new_y="NEXT")

    # Final Verdicts if available
    if "Final Verdict" in os_df.columns:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Final Verdict Distribution:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for verdict in ["CRITICAL", "UPGRADE NOW", "EXTEND + PLAN", "REPLACE", "CLOUD MIGRATE", "MONITOR"]:
            os_c = int((os_df.get("Final Verdict", pd.Series(dtype=str)).str.upper().str.startswith(verdict.split()[0])).sum())
            db_c = int((db_df.get("Final Verdict", pd.Series(dtype=str)).str.upper().str.startswith(verdict.split()[0])).sum()) if "Final Verdict" in db_df.columns else 0
            if os_c + db_c > 0:
                pdf.cell(0, 5, f"  {verdict}: {os_c + db_c} (OS: {os_c}, DB: {db_c})", new_x="LMARGIN", new_y="NEXT")

    # ── PAGE 3: CRITICAL ITEMS ───────────────────────────────────────────────
    pdf.add_page()
    pdf.section_header("2. Critical & High Risk Items", color=(153, 27, 27))

    urgent_items = []
    for df, type_label, name_col in [(os_df, "OS", "OS Version"), (db_df, "DB", "Database")]:
        if "Risk Score" in df.columns:
            for _, row in df.iterrows():
                score = row.get("Risk Score")
                if score is not None and score >= 50:
                    urgent_items.append({
                        "name": str(row.get(name_col, ""))[:35],
                        "type": type_label,
                        "risk": str(row.get("Risk Level", "")),
                        "score": int(score) if score else 0,
                        "days": row.get("Days Until EOL", ""),
                        "rec": str(row.get("Recommendation", ""))[:60],
                        "final": str(row.get("Final Verdict", ""))[:20],
                    })
    urgent_items.sort(key=lambda x: x["score"], reverse=True)

    if urgent_items:
        col_widths = [40, 10, 16, 12, 14, 50, 48]
        headers = ["Technology", "Type", "Risk", "Score", "Days", "Recommendation", "Final Verdict"]
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_fill_color(153, 27, 27)
        pdf.set_text_color(255, 255, 255)
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 6, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 6)
        for item in urgent_items[:30]:
            if item["risk"] == "CRITICAL":
                pdf.set_fill_color(255, 205, 210)
            elif item["risk"] == "HIGH":
                pdf.set_fill_color(255, 224, 178)
            else:
                pdf.set_fill_color(255, 249, 196)
            days_str = str(item["days"]) if item["days"] is not None else "N/A"
            vals = [item["name"], item["type"], item["risk"], str(item["score"]),
                    days_str, item["rec"], item["final"]]
            for w, v in zip(col_widths, vals):
                pdf.cell(w, 5, _safe(v), border=1, fill=True)
            pdf.ln()
    else:
        pdf.cell(0, 6, "No critical or high risk items found.", new_x="LMARGIN", new_y="NEXT")

    # ── PAGE 4: GUIDING PRINCIPLES ───────────────────────────────────────────
    if principles:
        pdf.add_page()
        pdf.section_header("3. Guiding Principles (from Policy Chat)", color=(6, 95, 70))
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 5, "These principles were generated from the interactive policy conversation with Agent 5.",
                new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        for gp in principles[:12]:
            pdf.set_font("Helvetica", "B", 9)
            cat = gp.get("category", "")
            pdf.cell(0, 5, _safe(f"{gp.get('code','')}: {gp.get('title','')}  [{cat}]"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 4, _safe(f"  Rule: {gp.get('rule','')}"))
            pdf.set_font("Helvetica", "I", 7)
            pdf.multi_cell(0, 3, _safe(f"  Trigger: {gp.get('trigger','')}"))
            pdf.ln(2)

    # ── PAGE 5: TECHNOLOGY DISPOSITION ────────────────────────────────────────
    if gp_table:
        pdf.add_page()
        pdf.section_header("4. Technology Disposition Table", color=(30, 58, 138))
        col_widths = [22, 30, 22, 53, 63]
        headers = ["Category", "Technology", "Cloud", "Upgrade Principle", "Replacement Principle"]
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_fill_color(30, 58, 138)
        pdf.set_text_color(255, 255, 255)
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 6, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 6)
        for i, row in enumerate(gp_table[:40]):
            bg = (248, 250, 252) if i % 2 == 0 else (255, 255, 255)
            pdf.set_fill_color(*bg)
            vals = [row.get("category","")[:12], row.get("technology","")[:18],
                    row.get("cloud_target","")[:12],
                    row.get("upgrade_principle","")[:50],
                    row.get("replacement_principle","")[:58]]
            for w, v in zip(col_widths, vals):
                pdf.cell(w, 5, _safe(v), border=1, fill=True)
            pdf.ln()

    # ── PAGE 6: COST ANALYSIS ────────────────────────────────────────────────
    if costed_data:
        pdf.add_page()
        pdf.section_header("5. Cost Analysis — Upgrade vs Replace vs Do Nothing", color=(146, 64, 14))
        col_widths = [35, 20, 35, 35, 35, 15, 15]
        headers = ["Technology", "Category", "Upgrade Cost", "Replace Cost", "Do Nothing", "Unit", "Source"]
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_fill_color(146, 64, 14)
        pdf.set_text_color(255, 255, 255)
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 6, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 6)
        for i, row in enumerate(costed_data[:35]):
            bg = (255, 251, 235) if i % 2 == 0 else (255, 247, 237)
            pdf.set_fill_color(*bg)
            vals = [row.get("technology","")[:22], row.get("category","")[:12],
                    row.get("cost_upgrade","")[:28], row.get("cost_replace","")[:28],
                    row.get("cost_do_nothing","")[:28], row.get("cost_unit","")[:8],
                    row.get("cost_source","")[:10]]
            for w, v in zip(col_widths, vals):
                pdf.cell(w, 5, _safe(v), border=1, fill=True)
            pdf.ln()

    # ── PAGE 7: VENDOR COST INTELLIGENCE ─────────────────────────────────────
    if costs:
        pdf.add_page()
        pdf.section_header("6. Live Vendor Cost Intelligence", color=(146, 64, 14))
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 5, "Researched by Agent 5 during the Policy Chat phase.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        for vendor, summary in costs.items():
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, _safe(f"{vendor}:"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 4, _safe(f"  {str(summary)[:200]}"))
            pdf.ln(2)

    # ── LAST PAGE: DISCLAIMER ────────────────────────────────────────────────
    pdf.add_page()
    pdf.section_header("Disclaimer & Methodology")
    pdf.set_font("Helvetica", "", 8)
    disclaimers = [
        "This report was generated by the INFY Migration Version Lifecycle Tracker using AI-powered analysis.",
        "All lifecycle dates are sourced from vendor documentation and internet verification by Agent 1 (Sentinel).",
        "Recommendations are generated by Agent 2 (Advisor) using OpenAI GPT and aligned with Guiding Principles.",
        "Cost estimates are approximate industry estimates for directional planning only.",
        "Actual costs vary by enterprise agreement, volume licensing, region, and application complexity.",
        "Compliance assessments are indicative and should be validated by your compliance team.",
        f"Report generated: {datetime.now().strftime('%d %B %Y %H:%M UTC')}",
        f"Project window: {project_start} to {project_end}",
        f"Portfolio size: {total_os} OS + {total_db} DB = {total_os+total_db} technologies tracked",
    ]
    for d in disclaimers:
        pdf.cell(0, 5, _safe(f"  - {d}"), new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.getvalue()
