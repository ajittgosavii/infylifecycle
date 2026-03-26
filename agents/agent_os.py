"""
Agent 1: Internet Change Verifier
==================================
The baseline_data.py already contains ALL known OS and DB versions.
Agent 1's ONLY job is to check internet for lifecycle date changes.

Uses OpenAI gpt-4o-mini (chat.completions) — no Responses API dependency.
"""

from openai import OpenAI
import json
from datetime import datetime


# ── Search targets — focused on finding date changes ─────────────────────────
OS_CHECK_TARGETS = [
    ("Windows 11/10 Client",
     "Windows 11 Windows 10 latest version lifecycle support end dates changed 2025 2026 microsoft.com"),
    ("Windows Server",
     "Windows Server 2016 2019 2022 2025 lifecycle support end dates microsoft.com"),
    ("RHEL",
     "Red Hat Enterprise Linux RHEL 7 8 9 10 end of life support dates changed 2026 redhat.com"),
    ("Ubuntu",
     "Ubuntu LTS 20.04 22.04 24.04 end of life support dates ubuntu.com 2026"),
    ("SLES",
     "SUSE Linux Enterprise Server SLES 12 15 all service packs lifecycle dates changed suse.com"),
    ("Debian",
     "Debian 10 11 12 13 end of life dates changed debian.org 2026"),
    ("CentOS Stream Rocky AlmaLinux Oracle Linux",
     "CentOS Stream 9 10 Rocky Linux AlmaLinux Oracle Linux lifecycle dates 2026"),
    ("macOS",
     "macOS Ventura Sonoma Sequoia support end dates Apple 2026"),
    ("Solaris AIX",
     "Oracle Solaris 11.4 IBM AIX 7.2 7.3 support end dates changed 2026"),
]

DB_CHECK_TARGETS = [
    ("SQL Server",
     "SQL Server 2016 2017 2019 2022 mainstream extended support end dates changed microsoft.com"),
    ("Oracle Database",
     "Oracle Database 19c 23ai premier extended support dates changed oracle.com 2026"),
    ("PostgreSQL MySQL MariaDB",
     "PostgreSQL 14 15 16 17 MySQL 8.0 8.4 MariaDB 10.11 11.4 end of life dates changed 2026"),
    ("IBM Db2 Informix SAP",
     "IBM Db2 11.5 IBM Informix 14.10 SAP HANA 2.0 SAP ASE 16 support dates changed 2026"),
    ("MongoDB Redis Cassandra",
     "MongoDB 7.0 8.0 Redis 7.4 Apache Cassandra 4.1 5.0 end of life dates 2026"),
    ("Amazon AWS databases",
     "Amazon Aurora RDS MySQL PostgreSQL end of support dates changed aws.amazon.com 2026"),
    ("Azure and Snowflake",
     "Azure SQL Managed Instance Cosmos DB Databricks Runtime end of support dates 2026"),
]

WS_CHECK_TARGETS = [
    ("IIS Nginx",
     "IIS 10.0 Nginx latest stable version lifecycle support end dates 2025 2026"),
    ("Apache HTTP Server",
     "Apache HTTP Server 2.4 end of life lifecycle dates changed apache.org 2026"),
]

AS_CHECK_TARGETS = [
    ("Tomcat JBoss WebSphere",
     "Apache Tomcat 9 10.1 11 JBoss EAP 7.4 8.0 IBM WebSphere 9 end of life support dates 2025 2026"),
    ("Kafka RabbitMQ ZooKeeper",
     "Apache Kafka 3.x RabbitMQ 3.13 ZooKeeper 3.8 end of life support dates 2026"),
    ("Kubernetes",
     "Kubernetes 1.30 1.31 1.32 end of life support dates kubernetes.io 2025 2026"),
]

FW_CHECK_TARGETS = [
    (".NET Framework and .NET",
     ".NET Framework 4.8 .NET 8 9 10 lifecycle end of support dates changed microsoft.com 2026"),
    ("Spring Boot PHP",
     "Spring Boot 3.3 3.4 PHP 8.2 8.3 8.4 end of life dates changed 2026"),
    ("React Angular Vue.js Node.js",
     "React 18 19 Angular 18 19 Vue.js 3 Node.js 20 22 end of life support dates 2026"),
    ("Java Python Django Rails",
     "Java JDK 17 21 Python 3.12 3.13 Django 5.2 Ruby on Rails 7 8 support end dates 2026"),
]


class OSDataAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model  = "gpt-4o-mini"   # chat.completions — widely available
        self.today  = datetime.now().strftime("%d %B %Y")

    def fetch_updates(self, progress_callback=None) -> dict:
        """
        Checks the internet for ANY changes to lifecycle dates.
        Returns a dict: family → result. Errors surfaced in progress messages.
        """
        updates    = {}
        ai_success = 0
        ai_failed  = 0
        all_targets = (
            [("OS", f, q) for f, q in OS_CHECK_TARGETS] +
            [("DB", f, q) for f, q in DB_CHECK_TARGETS] +
            [("WS", f, q) for f, q in WS_CHECK_TARGETS] +
            [("AS", f, q) for f, q in AS_CHECK_TARGETS] +
            [("FW", f, q) for f, q in FW_CHECK_TARGETS]
        )
        total = len(all_targets)

        for idx, (kind, family, query) in enumerate(all_targets):
            if progress_callback:
                progress_callback(
                    idx / total,
                    f"🔍 Calling OpenAI + web_search: {family}  ({idx+1}/{total})"
                )
            try:
                result = self._check_changes(kind, family, query)
                ai_success += 1
                if result.get("changes"):
                    updates[family] = result
                    if progress_callback:
                        progress_callback(
                            (idx+1) / total,
                            f"✅ {family}: {len(result['changes'])} change(s) found"
                        )
                else:
                    if progress_callback:
                        progress_callback(
                            (idx+1) / total,
                            f"✅ {family}: no changes — baseline data is current"
                        )
            except Exception as e:
                ai_failed += 1
                err_msg = str(e)[:80]
                updates[family] = {"error": err_msg, "changes": []}
                if progress_callback:
                    progress_callback(
                        (idx+1) / total,
                        f"⚠️ {family}: OpenAI error — {err_msg}"
                    )

        if progress_callback:
            if ai_failed == total:
                progress_callback(1.0,
                    f"❌ Agent 1 complete — OpenAI failed all {total} checks. "
                    f"Verify API key at platform.openai.com/usage")
            elif ai_failed > 0:
                progress_callback(1.0,
                    f"⚠️ Agent 1 complete — OpenAI: {ai_success} succeeded, "
                    f"{ai_failed} failed. {len([u for u in updates.values() if u.get('changes')])} families updated.")
            else:
                progress_callback(1.0,
                    f"✅ Agent 1 complete — OpenAI ran {ai_success} web checks. "
                    f"{len([u for u in updates.values() if u.get('changes')])} families had date changes.")

        return updates

    def _check_changes(self, kind: str, family: str, query: str) -> dict:
        prompt = f"""Search the internet for the LATEST support lifecycle dates for {family}.
Query: {query}

Today's date: {self.today}

Look specifically for any RECENT changes, corrections, or updates to support end dates.
Return ONLY a JSON object (no markdown):
{{
  "family": "{family}",
  "kind": "{kind}",
  "changes": [
    {{
      "name": "exact product/version name e.g. SQL Server 2016",
      "field": "which field changed e.g. Extended Support End",
      "new_value": "the correct current value e.g. 2026-07-14",
      "status": "Supported|End of Life|Expiring Soon|Future",
      "notes": "source or context"
    }}
  ]
}}

Only include entries where you found CONFIRMED current data from official sources.
If nothing has changed from known dates, return an empty changes array."""

        # OpenAI chat completions — no Responses API needed
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content or ""

        try:
            clean = text.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            start = clean.find("{")
            end   = clean.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(clean[start:end])
        except Exception:
            pass
        return {"family": family, "changes": []}

    def merge_updates_into_df(self, os_df, db_df, updates: dict,
                              ws_df=None, as_df=None, fw_df=None):
        """
        Apply web-verified date changes to OS, DB, WS, AS, FW dataframes.
        Updates the Notes column to show [Web verified: value].
        Returns (updated_os_df, updated_db_df, updated_ws_df, updated_as_df, updated_fw_df, changes_log).
        """
        import pandas as pd

        os_df   = os_df.copy()
        db_df   = db_df.copy()
        ws_df   = ws_df.copy() if ws_df is not None else pd.DataFrame()
        as_df   = as_df.copy() if as_df is not None else pd.DataFrame()
        fw_df   = fw_df.copy() if fw_df is not None else pd.DataFrame()
        changes = []

        # DB-style column map shared by DB, WS, AS, FW
        db_col_map = {
            "Mainstream":  "Mainstream / Premier End",
            "Extended":    "Extended Support End",
            "Status":      "Status",
        }

        def _update_db_style(target_df, name_col, kind_label, name, field, new_value, new_status):
            """Apply changes to a DB-style dataframe (DB/WS/AS/FW)."""
            if target_df.empty or name_col not in target_df.columns:
                return target_df
            # Build a composite search column
            if "Version" in target_df.columns:
                search_col = target_df[name_col] + " " + target_df["Version"]
            else:
                search_col = target_df[name_col]
            mask = (
                target_df[name_col].str.contains(name, case=False, na=False, regex=False) |
                search_col.str.contains(name, case=False, na=False, regex=False)
            )
            if mask.any():
                idx = target_df[mask].index[0]
                col = next((v for k, v in db_col_map.items() if k.lower() in field.lower()),
                           "Mainstream / Premier End")
                if col in target_df.columns:
                    old = target_df.at[idx, col]
                    if new_value and new_value != old:
                        target_df.at[idx, col] = new_value
                        note = str(target_df.at[idx, "Notes"] or "")
                        target_df.at[idx, "Notes"] = f"{note} [Web: {new_value}]".strip()
                        changes.append(f"{kind_label}: {name} | {col}: '{old}' → '{new_value}'")
                if new_status and "Status" in target_df.columns and new_status != target_df.at[idx, "Status"]:
                    old_s = target_df.at[idx, "Status"]
                    target_df.at[idx, "Status"] = new_status
                    changes.append(f"{kind_label}: {name} | Status: '{old_s}' → '{new_status}'")
            return target_df

        for family, result in updates.items():
            if not result.get("changes"):
                continue

            kind = result.get("kind", "OS")

            for change in result["changes"]:
                name      = change.get("name", "")
                field     = change.get("field", "")
                new_value = change.get("new_value", "")
                new_status= change.get("status", "")

                if not name or not new_value:
                    continue

                # Try OS dataframe
                if kind == "OS" or kind == "both":
                    mask = os_df["OS Version"].str.contains(
                        name.replace("(", r"\(").replace(")", r"\)"),
                        case=False, na=False, regex=True
                    )
                    if mask.any():
                        idx = os_df[mask].index[0]
                        col_map = {
                            "Mainstream": "Mainstream/Full Support End",
                            "Extended":   "Extended/LTSC Support End",
                            "Security":   "Security/Standard Support End",
                            "Availability":"Availability Date",
                        }
                        col = next((v for k, v in col_map.items() if k.lower() in field.lower()),
                                   "Mainstream/Full Support End")
                        old = os_df.at[idx, col]
                        if new_value and new_value != old:
                            os_df.at[idx, col] = new_value
                            note = str(os_df.at[idx, "Notes"] or "")
                            os_df.at[idx, "Notes"] = f"{note} [Web: {new_value}]".strip()
                            changes.append(f"OS: {name} | {col}: '{old}' → '{new_value}'")

                # Try DB dataframe
                if kind == "DB" or kind == "both":
                    db_df = _update_db_style(db_df, "Database", "DB", name, field, new_value, new_status)

                # Try WS dataframe
                if kind == "WS" or kind == "both":
                    ws_df = _update_db_style(ws_df, "Web Server", "WS", name, field, new_value, new_status)

                # Try AS dataframe
                if kind == "AS" or kind == "both":
                    as_df = _update_db_style(as_df, "App Server", "AS", name, field, new_value, new_status)

                # Try FW dataframe
                if kind == "FW" or kind == "both":
                    fw_df = _update_db_style(fw_df, "Framework", "FW", name, field, new_value, new_status)

        return os_df, db_df, ws_df, as_df, fw_df, changes
