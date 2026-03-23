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


def export_to_excel(
    os_df: pd.DataFrame,
    db_df: pd.DataFrame,
    generated_at: str = None,
    version_history: list = None   # list of version dicts from VersionGuardianAgent
) -> bytes:
    """
    Build and return formatted .xlsx as bytes.

    Sheet layout:
      Sheet 1  — OS Versions (current / latest)
      Sheet 2  — DB Versions (current / latest)
      Sheet 3  — Summary + Agent registry
      Sheet 4+ — One OS+DB history sheet per version (Agent 4)
                 named "v1 OS", "v1 DB", "v2 OS", "v2 DB", ...
    """
    wb = Workbook()
    ts = generated_at or datetime.now().strftime("%d %b %Y %H:%M UTC")

    # ── Sheet 1 — Current OS Versions ────────────────────────────────────────
    ws_os = wb.active
    ws_os.title = "OS Versions"
    _write_sheet(ws_os, os_df,
                 title=f"OS Versions (current)  —  INFY Migration Reference  |  {ts}",
                 status_col=None, rec_col="Recommendation")

    # ── Sheet 2 — Current DB Versions ────────────────────────────────────────
    ws_db = wb.create_sheet("DB Versions")
    _write_sheet(ws_db, db_df,
                 title=f"DB Versions (current)  —  INFY Migration Reference  |  {ts}",
                 status_col="Status", rec_col="Recommendation")

    # ── Sheet 3 — Summary ────────────────────────────────────────────────────
    ws_s = wb.create_sheet("Summary")
    history_note = (
        f"{len(version_history)} version(s) stored — see sheets v1 OS / v1 DB etc."
        if version_history else "No prior versions (first run)"
    )
    summary_rows = [
        ("", ""),
        ("INFY Migration Version Lifecycle Tracker", ""),
        ("", ""),
        ("Generated on",        ts),
        ("OS Versions (rows)",  str(len(os_df))),
        ("DB Versions (rows)",  str(len(db_df))),
        ("Version history",     history_note),
        ("", ""),
        ("Agent 1", "Dynamically fetches ALL OS & DB lifecycle data from the web via Claude AI web search"),
        ("Agent 2", "Generates expert AI recommendations per row — powered by Claude claude-opus-4-20250514"),
        ("Agent 3", "Bi-weekly refresh monitor — seeks user permission before re-running fetch + recommendations"),
        ("Agent 4", "Version Guardian — snapshots data before every refresh, appends new data, never overwrites"),
        ("", ""),
        ("AI Model",    "Claude claude-opus-4-20250514 (Anthropic)"),
        ("Data Source", "Live web search via Claude AI — Microsoft, Red Hat, Ubuntu, Oracle, PostgreSQL.org and others"),
        ("", ""),
        ("OS Families",
         "Windows 10/11 Client, Windows Server 2003–2025, RHEL 4–10, Ubuntu LTS 14.04–24.04, "
         "SLES 11–16 all SPs, Debian 8–13, CentOS 6–Stream 10, Rocky/AlmaLinux 8–10, "
         "Oracle Linux 6–10, openSUSE Leap, Fedora, macOS, Solaris, AIX, HP-UX, FreeBSD, OpenVMS, Tru64, Android, iOS"),
        ("DB Products",
         "SQL Server, Oracle DB, PostgreSQL, MySQL, MariaDB, MongoDB, Redis, IBM Db2, Cassandra, "
         "Elasticsearch, SAP HANA, SAP ASE, Teradata, Aurora, RDS, CouchDB, Couchbase, Neo4j, "
         "InfluxDB, TimescaleDB, Snowflake, Databricks, Azure SQL, Cosmos DB"),
    ]

    ws_s.column_dimensions["A"].width = 28
    ws_s.column_dimensions["B"].width = 82

    for ri, (label, value) in enumerate(summary_rows, 1):
        ca = ws_s.cell(row=ri, column=1, value=label)
        cb = ws_s.cell(row=ri, column=2, value=value)
        if ri == 2:
            ca.font = Font(bold=True, size=14, color=INFY_NAVY, name="Calibri")
            ws_s.merge_cells(f"A{ri}:B{ri}")
            ca.alignment = CENTER
        elif label in ("Agent 1", "Agent 2", "Agent 3", "Agent 4"):
            ca.font = Font(bold=True, size=11, color=INFY_BLUE, name="Calibri")
            cb.font = Font(size=11, name="Calibri")
        elif label:
            ca.font = Font(bold=True, size=11, name="Calibri")
            cb.font = Font(size=11, name="Calibri")
        ws_s.row_dimensions[ri].height = 20

    # ── Sheets 4+ — One OS+DB sheet per historical version (Agent 4) ─────────
    if version_history:
        for snap in version_history:
            vnum  = snap.get("version", "?")
            vlabel = snap.get("label", f"v{vnum}")
            vts    = snap["timestamp"].strftime("%d %b %Y %H:%M") if "timestamp" in snap else ""

            # OS history sheet  e.g. "v1 OS"
            ws_vos = wb.create_sheet(f"v{vnum} OS")
            _write_sheet(
                ws_vos,
                snap["os_df"],
                title=f"OS Versions — {vlabel}  ({snap.get('os_count',0)} rows)",
                status_col=None,
                rec_col="Recommendation"
            )
            # Stamp version info in cell A1 area above the title
            ws_vos.insert_rows(1)
            ws_vos.cell(row=1, column=1,
                        value=f"Snapshot: {vlabel}  |  Saved by Agent 4  |  {vts}").font = Font(
                            italic=True, size=10, color="555555", name="Calibri")

            # DB history sheet  e.g. "v1 DB"
            ws_vdb = wb.create_sheet(f"v{vnum} DB")
            _write_sheet(
                ws_vdb,
                snap["db_df"],
                title=f"DB Versions — {vlabel}  ({snap.get('db_count',0)} rows)",
                status_col="Status",
                rec_col="Recommendation"
            )
            ws_vdb.insert_rows(1)
            ws_vdb.cell(row=1, column=1,
                        value=f"Snapshot: {vlabel}  |  Saved by Agent 4  |  {vts}").font = Font(
                            italic=True, size=10, color="555555", name="Calibri")

            # Change log sheet  e.g. "v1 Changes"
            if snap.get("changes"):
                ws_chg = wb.create_sheet(f"v{vnum} Changes")
                ws_chg.column_dimensions["A"].width = 100
                ws_chg.cell(row=1, column=1,
                            value=f"Change log — {vlabel}").font = Font(
                                bold=True, size=12, color=INFY_NAVY, name="Calibri")
                ws_chg.row_dimensions[1].height = 22
                for ci, change in enumerate(snap["changes"], 2):
                    c = ws_chg.cell(row=ci, column=1, value=change)
                    c.font = Font(size=10, name="Calibri")
                    c.alignment = LEFT
                    ws_chg.row_dimensions[ci].height = 16

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
