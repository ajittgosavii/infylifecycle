"""
Excel Export Utility
Generates a formatted .xlsx file with OS Versions and DB Versions sheets,
including colour-coded status cells, bold headers, and auto-column widths.
"""
import io
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter
from datetime import datetime


# ── Colour palette ──────────────────────────────────────────────────────────
HEADER_FILL   = PatternFill("solid", fgColor="003087")   # Infosys navy
HEADER_FONT   = Font(bold=True, color="FFFFFF", size=11, name="Calibri")
ALT_ROW_FILL  = PatternFill("solid", fgColor="EEF2F7")   # light blue-grey
WHITE_FILL    = PatternFill("solid", fgColor="FFFFFF")

REC_FILL      = PatternFill("solid", fgColor="FFF9C4")   # pale yellow for Recommendation

STATUS_FILLS = {
    "end of life":    PatternFill("solid", fgColor="FFCDD2"),  # red-50
    "expiring soon":  PatternFill("solid", fgColor="FFE0B2"),  # orange-100
    "supported":      PatternFill("solid", fgColor="C8E6C9"),  # green-100
    "future":         PatternFill("solid", fgColor="E3F2FD"),  # blue-50
}

THIN_BORDER = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT   = Alignment(horizontal="left",   vertical="center", wrap_text=True)


def _write_sheet(ws, df: pd.DataFrame, title: str, status_col: str = None,
                 rec_col: str = "Recommendation"):
    """Write a dataframe to a worksheet with full formatting."""
    cols = list(df.columns)

    # ── Title row ────────────────────────────────────────────────────────────
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(cols))
    title_cell = ws.cell(row=1, column=1, value=title)
    title_cell.font = Font(bold=True, size=13, name="Calibri", color="FFFFFF")
    title_cell.fill = PatternFill("solid", fgColor="001F5B")
    title_cell.alignment = CENTER
    ws.row_dimensions[1].height = 28

    # ── Header row ────────────────────────────────────────────────────────────
    for col_idx, col_name in enumerate(cols, start=1):
        cell = ws.cell(row=2, column=col_idx, value=col_name)
        cell.font  = HEADER_FONT
        cell.fill  = HEADER_FILL
        cell.alignment = CENTER
        cell.border = THIN_BORDER
    ws.row_dimensions[2].height = 24

    # ── Data rows ────────────────────────────────────────────────────────────
    for row_idx, (_, row) in enumerate(df.iterrows(), start=3):
        fill = ALT_ROW_FILL if row_idx % 2 == 0 else WHITE_FILL

        for col_idx, col_name in enumerate(cols, start=1):
            val = row[col_name]
            if pd.isna(val):
                val = ""
            cell = ws.cell(row=row_idx, column=col_idx, value=str(val) if val != "" else "")
            cell.border = THIN_BORDER
            cell.alignment = LEFT if col_name in (rec_col, "Notes") else CENTER

            # Colour overrides
            if col_name == rec_col:
                cell.fill = REC_FILL
                cell.font = Font(name="Calibri", size=10)
            elif status_col and col_name == status_col:
                status_key = str(val).lower()
                cell.fill = STATUS_FILLS.get(status_key, fill)
                cell.font = Font(bold=True, name="Calibri", size=10)
            else:
                cell.fill = fill
                cell.font = Font(name="Calibri", size=10)

        ws.row_dimensions[row_idx].height = 18

    # ── Column widths ────────────────────────────────────────────────────────
    for col_idx, col_name in enumerate(cols, start=1):
        col_letter = get_column_letter(col_idx)
        if col_name in (rec_col, "Notes"):
            ws.column_dimensions[col_letter].width = 50
        elif "Date" in col_name or "End" in col_name:
            ws.column_dimensions[col_letter].width = 22
        elif col_name in ("Upgrade", "Replace"):
            ws.column_dimensions[col_letter].width = 10
        else:
            max_len = max(
                len(str(col_name)),
                df[col_name].astype(str).str.len().max() if len(df) > 0 else 0
            )
            ws.column_dimensions[col_letter].width = min(max_len + 4, 40)

    # ── Freeze panes ────────────────────────────────────────────────────────
    ws.freeze_panes = "A3"


def export_to_excel(os_df: pd.DataFrame, db_df: pd.DataFrame,
                    generated_at: str = None) -> bytes:
    """
    Build and return an .xlsx file as bytes containing two formatted sheets.

    Args:
        os_df: OS Versions dataframe
        db_df: DB Versions dataframe
        generated_at: optional timestamp string for the cover note

    Returns:
        bytes: The Excel file as a bytes object
    """
    wb = Workbook()

    # ── Sheet 1: OS Versions ─────────────────────────────────────────────────
    ws_os = wb.active
    ws_os.title = "OS Versions"
    _write_sheet(
        ws_os, os_df,
        title=f"OS Versions — INFY Migration Reference Data",
        status_col=None,
        rec_col="Recommendation"
    )

    # ── Sheet 2: DB Versions ─────────────────────────────────────────────────
    ws_db = wb.create_sheet("DB Versions")
    _write_sheet(
        ws_db, db_df,
        title="DB Versions — INFY Migration Reference Data",
        status_col="Status",
        rec_col="Recommendation"
    )

    # ── Sheet 3: Summary / Cover ──────────────────────────────────────────────
    ws_cover = wb.create_sheet("Summary")
    ts = generated_at or datetime.now().strftime("%d %b %Y %H:%M UTC")

    summary_rows = [
        ("", ""),
        ("INFY Migration Reference — Version Lifecycle Tracker", ""),
        ("", ""),
        ("Generated on", ts),
        ("OS Versions (rows)", str(len(os_df))),
        ("DB Versions (rows)", str(len(db_df))),
        ("", ""),
        ("Agent 1", "OS & DB data fetched and verified via web search (Claude AI)"),
        ("Agent 2", "AI-generated expert recommendations per OS/DB entry (Claude AI)"),
        ("Agent 3", "Bi-weekly refresh monitor — seeks permission before re-running"),
        ("", ""),
        ("Data Source", "INFY_Migration_Reference_Data, Infosys Enterprise Architecture"),
        ("AI Model", "Claude claude-opus-4-20250514 (Anthropic)"),
    ]

    ws_cover.column_dimensions["A"].width = 32
    ws_cover.column_dimensions["B"].width = 72

    for r_idx, (label, value) in enumerate(summary_rows, start=1):
        cell_a = ws_cover.cell(row=r_idx, column=1, value=label)
        cell_b = ws_cover.cell(row=r_idx, column=2, value=value)

        if r_idx == 2:  # Title row
            cell_a.font = Font(bold=True, size=14, name="Calibri", color="001F5B")
            ws_cover.merge_cells(f"A{r_idx}:B{r_idx}")
            cell_a.alignment = CENTER
        elif label in ("Agent 1", "Agent 2", "Agent 3"):
            cell_a.font = Font(bold=True, size=11, name="Calibri", color="003087")
            cell_b.font = Font(size=11, name="Calibri")
        elif label:
            cell_a.font = Font(bold=True, size=11, name="Calibri")
            cell_b.font = Font(size=11, name="Calibri")

        ws_cover.row_dimensions[r_idx].height = 20

    # ── Save to bytes ────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
