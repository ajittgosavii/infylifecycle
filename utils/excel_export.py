"""
Excel Export Utility
Generates a polished .xlsx with OS Versions, DB Versions, and Summary sheets.
All data comes from live-fetched dataframes — no hardcoded content.
"""

import io
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

# ── Colour constants ─────────────────────────────────────────────────────────
INFY_NAVY     = "001F5B"
INFY_BLUE     = "003087"
HDR_FONT      = Font(bold=True, color="FFFFFF", size=11, name="Calibri")
HDR_FILL      = PatternFill("solid", fgColor=INFY_BLUE)
TITLE_FILL    = PatternFill("solid", fgColor=INFY_NAVY)
ALT_FILL      = PatternFill("solid", fgColor="EEF2F7")
WHITE_FILL    = PatternFill("solid", fgColor="FFFFFF")
REC_FILL      = PatternFill("solid", fgColor="FFF9C4")

STATUS_FILL = {
    "end of life":    PatternFill("solid", fgColor="FFCDD2"),
    "expiring soon":  PatternFill("solid", fgColor="FFE0B2"),
    "supported":      PatternFill("solid", fgColor="C8E6C9"),
    "future":         PatternFill("solid", fgColor="E3F2FD"),
    "active":         PatternFill("solid", fgColor="C8E6C9"),
}

THIN = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT   = Alignment(horizontal="left",   vertical="center", wrap_text=True)


def _write_sheet(ws, df: pd.DataFrame, title: str,
                 status_col: str = None, rec_col: str = "Recommendation"):
    cols = list(df.columns)

    # Title row
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(cols))
    tc = ws.cell(row=1, column=1, value=title)
    tc.font      = Font(bold=True, size=13, color="FFFFFF", name="Calibri")
    tc.fill      = TITLE_FILL
    tc.alignment = CENTER
    ws.row_dimensions[1].height = 28

    # Header row
    for ci, col in enumerate(cols, 1):
        c = ws.cell(row=2, column=ci, value=col)
        c.font = HDR_FONT; c.fill = HDR_FILL
        c.alignment = CENTER; c.border = THIN
    ws.row_dimensions[2].height = 24

    # Data rows
    for ri, (_, row) in enumerate(df.iterrows(), 3):
        base_fill = ALT_FILL if ri % 2 == 0 else WHITE_FILL
        for ci, col in enumerate(cols, 1):
            val = row[col]
            val = "" if pd.isna(val) else str(val)
            c = ws.cell(row=ri, column=ci, value=val)
            c.border = THIN
            c.alignment = LEFT if col in (rec_col, "Notes") else CENTER

            if col == rec_col:
                c.fill = REC_FILL
                c.font = Font(name="Calibri", size=10)
            elif status_col and col == status_col:
                c.fill = STATUS_FILL.get(val.lower(), base_fill)
                c.font = Font(bold=True, name="Calibri", size=10)
            else:
                c.fill = base_fill
                c.font = Font(name="Calibri", size=10)
        ws.row_dimensions[ri].height = 18

    # Column widths
    for ci, col in enumerate(cols, 1):
        cl = get_column_letter(ci)
        if col in (rec_col, "Notes"):
            ws.column_dimensions[cl].width = 55
        elif any(k in col for k in ("Date", "End", "Support")):
            ws.column_dimensions[cl].width = 22
        elif col in ("Upgrade", "Replace"):
            ws.column_dimensions[cl].width = 10
        elif col in ("OS Version", "Database"):
            ws.column_dimensions[cl].width = 26
        else:
            max_len = max(len(col),
                          df[col].astype(str).str.len().max() if len(df) else 0)
            ws.column_dimensions[cl].width = min(max_len + 4, 38)

    ws.freeze_panes = "A3"


def export_to_excel(os_df: pd.DataFrame, db_df: pd.DataFrame,
                    generated_at: str = None,
                    principles: list = None,
                    costs: dict = None,
                    version_history: list = None) -> bytes:
    """Build and return formatted .xlsx as bytes."""
    wb  = Workbook()
    ts  = generated_at or datetime.now().strftime("%d %b %Y %H:%M UTC")

    # Sheet 1 — OS Versions
    ws_os = wb.active
    ws_os.title = "OS Versions"
    _write_sheet(ws_os, os_df,
                 title=f"OS Versions — INFY Migration Reference  |  {ts}",
                 status_col=None, rec_col="Recommendation")

    # Sheet 2 — DB Versions
    ws_db = wb.create_sheet("DB Versions")
    _write_sheet(ws_db, db_df,
                 title=f"DB Versions — INFY Migration Reference  |  {ts}",
                 status_col="Status", rec_col="Recommendation")

    # Sheet 3 — Summary
    ws_s = wb.create_sheet("Summary")
    rows = [
        ("", ""),
        ("INFY Migration Version Lifecycle Tracker", ""),
        ("", ""),
        ("Generated on",        ts),
        ("OS Versions (rows)",  str(len(os_df))),
        ("DB Versions (rows)",  str(len(db_df))),
        ("Project Window",      "1 April 2026 → 30 June 2028"),
        ("", ""),
        ("Agent 1", "Fetches ALL OS & DB lifecycle data live from the web via Claude AI (no hardcoded data)"),
        ("Agent 2", "Generates expert AI recommendations per row — Claude claude-opus-4-20250514"),
        ("Agent 3", "14-day refresh monitor — seeks permission before re-running"),
        ("Agent 4", "Version Guardian — snapshots data before every refresh"),
        ("Agent 5", "Policy Analysis — org interview → guiding principles → cost data → verdicts"),
        ("", ""),
        ("AI Model",    "Claude claude-opus-4-20250514 (Anthropic)"),
        ("Data Source", "Live web search via Claude AI — Microsoft, Red Hat, Ubuntu, Oracle, postgresql.org and others"),
    ]

    ws_s.column_dimensions["A"].width = 30
    ws_s.column_dimensions["B"].width = 80

    for ri, (label, value) in enumerate(rows, 1):
        ca = ws_s.cell(row=ri, column=1, value=label)
        cb = ws_s.cell(row=ri, column=2, value=value)
        if ri == 2:
            ca.font = Font(bold=True, size=14, color=INFY_NAVY, name="Calibri")
            ws_s.merge_cells(f"A{ri}:B{ri}")
            ca.alignment = CENTER
        elif label in ("Agent 1", "Agent 2", "Agent 3", "Agent 4", "Agent 5"):
            ca.font = Font(bold=True, size=11, color=INFY_BLUE, name="Calibri")
            cb.font = Font(size=11, name="Calibri")
        elif label:
            ca.font = Font(bold=True, size=11, name="Calibri")
            cb.font = Font(size=11, name="Calibri")
        ws_s.row_dimensions[ri].height = 20

    # Sheet 4 — Guiding Principles (Agent 5)
    if principles:
        ws_gp = wb.create_sheet("Guiding Principles")
        ws_gp.column_dimensions["A"].width = 10
        ws_gp.column_dimensions["B"].width = 28
        ws_gp.column_dimensions["C"].width = 55
        ws_gp.column_dimensions["D"].width = 48
        for ci, h in enumerate(["Code", "Title", "Rule", "Trigger"], 1):
            c = ws_gp.cell(row=1, column=ci, value=h)
            c.font = HDR_FONT; c.fill = HDR_FILL; c.alignment = CENTER; c.border = THIN
        for ri, gp in enumerate(principles, 2):
            fill = ALT_FILL if ri % 2 == 0 else WHITE_FILL
            for ci, key in enumerate(["code","title","rule","trigger"], 1):
                c = ws_gp.cell(row=ri, column=ci, value=gp.get(key, ""))
                c.font = Font(name="Calibri", size=10)
                c.fill = fill; c.border = THIN
                c.alignment = LEFT if ci > 1 else CENTER
            ws_gp.row_dimensions[ri].height = 16

    # Sheet 5 — Vendor Cost Data (Agent 5)
    if costs:
        ws_cost = wb.create_sheet("Vendor Cost Data")
        ws_cost.column_dimensions["A"].width = 28
        ws_cost.column_dimensions["B"].width = 88
        for ci, h in enumerate(["Vendor", "Cost Summary"], 1):
            c = ws_cost.cell(row=1, column=ci, value=h)
            c.font = HDR_FONT; c.fill = HDR_FILL; c.alignment = CENTER; c.border = THIN
        for ri, (vendor, summary) in enumerate(costs.items(), 2):
            fill = ALT_FILL if ri % 2 == 0 else WHITE_FILL
            cv = ws_cost.cell(row=ri, column=1, value=vendor)
            cs = ws_cost.cell(row=ri, column=2, value=summary)
            for c in (cv, cs):
                c.font = Font(name="Calibri", size=10)
                c.fill = fill; c.border = THIN; c.alignment = LEFT
            ws_cost.row_dimensions[ri].height = 18

    # Sheet 6 — Version History (Agent 4)
    if version_history:
        for snap in version_history:
            sheet_name = snap["label"][:31]  # Excel tab limit
            # OS snapshot
            ws_snap_os = wb.create_sheet(f"{sheet_name[:26]} OS")
            _write_sheet(ws_snap_os, snap["os_df"],
                         title=f"OS Snapshot — {snap['label']}",
                         status_col=None, rec_col="Recommendation")
            # DB snapshot
            ws_snap_db = wb.create_sheet(f"{sheet_name[:26]} DB")
            _write_sheet(ws_snap_db, snap["db_df"],
                         title=f"DB Snapshot — {snap['label']}",
                         status_col="Status", rec_col="Recommendation")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
