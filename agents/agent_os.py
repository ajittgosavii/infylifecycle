"""
Agent 1: Dynamic OS & DB Data Fetcher
Comprehensively searches the internet for ALL OS and DB lifecycle data.
NO hardcoded baseline — every row is fetched live from the web.
"""

import anthropic
import json
import pandas as pd
from datetime import datetime

# ── OS search targets ────────────────────────────────────────────────────────
OS_SEARCH_TARGETS = [
    {
        "family": "Windows 11 Client",
        "query": "Windows 11 all versions lifecycle support end dates mainstream extended site:microsoft.com",
        "hint": "Include ALL Windows 11 versions: 21H2, 22H2, 23H2, 24H2, 25H2, 26H1 and all editions"
    },
    {
        "family": "Windows 10 Client",
        "query": "Windows 10 all versions lifecycle support end dates mainstream extended LTSC microsoft",
        "hint": "Include 1507,1511,1607,1703,1709,1803,1809,1903,1909,2004,20H2,21H1,21H2,22H2 and all LTSC editions"
    },
    {
        "family": "Windows Server",
        "query": "Windows Server 2008 2012 2016 2019 2022 2025 lifecycle support end dates microsoft",
        "hint": "Include Windows Server 2003,2008,2008R2,2012,2012R2,2016,2019,2022,2025 all editions"
    },
    {
        "family": "RHEL",
        "query": "Red Hat Enterprise Linux RHEL all versions lifecycle support end dates redhat.com",
        "hint": "Include RHEL 4,5,6,7,8,9,10 with Full Support, Maintenance, and Extended Life Phase dates"
    },
    {
        "family": "Ubuntu",
        "query": "Ubuntu LTS non-LTS all releases lifecycle end of support dates ubuntu.com",
        "hint": "Include Ubuntu 14.04,16.04,18.04,20.04,22.04,24.04,24.10,25.04 LTS and interim releases"
    },
    {
        "family": "SLES",
        "query": "SUSE Linux Enterprise Server all versions service packs lifecycle support dates suse.com",
        "hint": "Include SLES 11,12,15 with all service packs SP1-SP7 and LTSS extended support dates"
    },
    {
        "family": "Debian",
        "query": "Debian Linux all releases lifecycle end of life support LTS ELTS dates debian.org",
        "hint": "Include Debian 8 Jessie through Debian 13 Trixie with security, LTS, and ELTS dates"
    },
    {
        "family": "CentOS",
        "query": "CentOS all versions end of life dates centos.org including CentOS Stream",
        "hint": "Include CentOS 6,7,8 and CentOS Stream 8,9,10 with EOL dates"
    },
    {
        "family": "Rocky and AlmaLinux",
        "query": "Rocky Linux AlmaLinux all versions lifecycle end of life support dates 2026",
        "hint": "Include Rocky Linux 8,9,10 and AlmaLinux 8,9,10 with detailed EOL dates"
    },
    {
        "family": "Oracle Linux",
        "query": "Oracle Linux all versions lifecycle premier extended support end dates oracle.com",
        "hint": "Include Oracle Linux 6,7,8,9,10 with Premier and Extended support end dates"
    },
    {
        "family": "openSUSE and Fedora",
        "query": "openSUSE Leap all versions Fedora Linux all releases lifecycle end of life dates 2026",
        "hint": "Include openSUSE Leap 15.x and Fedora 38,39,40,41,42 with EOL dates"
    },
    {
        "family": "macOS",
        "query": "macOS all versions lifecycle support end dates Apple 2026",
        "hint": "Include macOS 10.14 Mojave through macOS 15 Sequoia and macOS 26 with support end dates"
    },
    {
        "family": "Solaris",
        "query": "Oracle Solaris 10 11 all versions lifecycle support end dates oracle.com",
        "hint": "Include Solaris 10 and Solaris 11.1 through 11.4 SRU versions with support end dates"
    },
    {
        "family": "AIX",
        "query": "IBM AIX all versions technology levels lifecycle support end of service dates ibm.com",
        "hint": "Include AIX 6.1, 7.1, 7.2, 7.3 with all TL (Technology Level) versions and support dates"
    },
    {
        "family": "HP-UX",
        "query": "HP-UX 11i all versions lifecycle support end dates hpe.com",
        "hint": "Include HP-UX 11i v1, v2, v3 for both HP 9000 PA-RISC and Integrity Itanium servers"
    },
    {
        "family": "FreeBSD",
        "query": "FreeBSD all stable release branches lifecycle end of life dates freebsd.org",
        "hint": "Include FreeBSD 11,12,13,14,15 release and stable branches with EoL dates"
    },
    {
        "family": "OpenVMS and Tru64",
        "query": "OpenVMS VSI VMS Software Tru64 UNIX all versions lifecycle support dates 2026",
        "hint": "Include OpenVMS x86, IA-64, Alpha versions and Tru64 UNIX 5.x with support dates"
    },
    {
        "family": "Android and iOS",
        "query": "Android enterprise iOS iPadOS all versions security update support end dates 2026",
        "hint": "Include Android 10-15 enterprise and iOS/iPadOS 15-18 with Apple/Google support end dates"
    },
]

# ── DB search targets ────────────────────────────────────────────────────────
DB_SEARCH_TARGETS = [
    {
        "family": "SQL Server",
        "query": "Microsoft SQL Server all versions lifecycle mainstream extended end of support dates microsoft.com",
        "hint": "Include SQL Server 2008,2008R2,2012,2014,2016,2017,2019,2022,2025 with all support phase dates"
    },
    {
        "family": "Oracle Database",
        "query": "Oracle Database all versions premier extended lifecycle support end dates oracle.com 2026",
        "hint": "Include Oracle DB 10g,11g R1/R2,12c R1/R2,18c,19c,21c,23ai with all support phase dates"
    },
    {
        "family": "PostgreSQL",
        "query": "PostgreSQL all versions end of life support dates postgresql.org 2026",
        "hint": "Include PostgreSQL 9.6 through 18 with each version's EOL date"
    },
    {
        "family": "MySQL",
        "query": "MySQL all versions lifecycle premier extended support end dates oracle.com mysql.com",
        "hint": "Include MySQL 5.6, 5.7, 8.0, 8.4 LTS, 9.x LTS with all support phase dates"
    },
    {
        "family": "MariaDB",
        "query": "MariaDB all versions lifecycle end of life support dates mariadb.org 2026",
        "hint": "Include MariaDB 10.3 through 11.x including all LTS versions with EOL dates"
    },
    {
        "family": "MongoDB",
        "query": "MongoDB all versions lifecycle end of life support dates mongodb.com 2026",
        "hint": "Include MongoDB 3.6,4.0,4.2,4.4,5.0,6.0,7.0,8.0 with EOL dates"
    },
    {
        "family": "Redis",
        "query": "Redis all versions lifecycle end of life support dates redis.io 2026",
        "hint": "Include Redis 5.0,6.0,6.2,7.0,7.2,7.4,7.8,8.0 with EOL dates"
    },
    {
        "family": "IBM Db2",
        "query": "IBM Db2 all versions lifecycle end of support dates ibm.com 2026",
        "hint": "Include IBM Db2 9.7,10.1,10.5,11.1,11.5 with all support end dates"
    },
    {
        "family": "Cassandra",
        "query": "Apache Cassandra all versions lifecycle end of life support dates cassandra.apache.org",
        "hint": "Include Cassandra 3.0,3.11,4.0,4.1,5.0 with EOL dates"
    },
    {
        "family": "Elasticsearch",
        "query": "Elasticsearch Elastic Stack all versions end of life support dates elastic.co 2026",
        "hint": "Include Elasticsearch 6.x,7.x,8.x versions with EOL dates"
    },
    {
        "family": "SAP HANA",
        "query": "SAP HANA database all versions lifecycle end of maintenance support dates sap.com",
        "hint": "Include SAP HANA 1.0 SPS, 2.0 SPS revisions with Mainstream and Extended Maintenance dates"
    },
    {
        "family": "Sybase SAP ASE",
        "query": "SAP Sybase Adaptive Server Enterprise ASE all versions lifecycle end of support dates sap.com",
        "hint": "Include Sybase ASE 15.0,15.5,15.7,16.0 versions with PAM support end dates"
    },
    {
        "family": "Teradata",
        "query": "Teradata Database Vantage all versions lifecycle end of support dates teradata.com",
        "hint": "Include Teradata Database 14.x,15.x,16.x and Vantage versions with support dates"
    },
    {
        "family": "Amazon Aurora",
        "query": "Amazon Aurora MySQL PostgreSQL compatible all versions end of support lifecycle aws.amazon.com 2026",
        "hint": "Include Aurora MySQL 2.x,3.x and Aurora PostgreSQL major version support end dates"
    },
    {
        "family": "Amazon RDS",
        "query": "Amazon RDS engine versions end of support deprecation dates aws.amazon.com 2026",
        "hint": "Include RDS SQL Server, MySQL, PostgreSQL, MariaDB, Oracle engine version deprecation dates"
    },
    {
        "family": "CouchDB and CouchBase",
        "query": "Apache CouchDB Couchbase Server all versions lifecycle end of support dates 2026",
        "hint": "Include CouchDB 2.x,3.x and Couchbase Server 6.x,7.x with EOL dates"
    },
    {
        "family": "Neo4j",
        "query": "Neo4j graph database all versions lifecycle end of life support dates neo4j.com 2026",
        "hint": "Include Neo4j 3.5,4.x,5.x with all support end dates"
    },
    {
        "family": "InfluxDB and TimescaleDB",
        "query": "InfluxDB TimescaleDB all versions lifecycle end of support dates influxdata.com 2026",
        "hint": "Include InfluxDB 1.x,2.x,3.x and TimescaleDB versions with support dates"
    },
    {
        "family": "Snowflake and Databricks",
        "query": "Snowflake Databricks Runtime versions lifecycle end of support dates 2026",
        "hint": "Include Databricks Runtime LTS versions with support end dates and Snowflake versioning policy"
    },
    {
        "family": "Azure SQL and Cosmos DB",
        "query": "Azure SQL Database Cosmos DB versions end of support lifecycle microsoft.com 2026",
        "hint": "Include Azure SQL Database and Cosmos DB API version deprecation and support end dates"
    },
]

OS_COLUMNS = [
    "OS Version", "Availability Date", "Security/Standard Support End",
    "Mainstream/Full Support End", "Extended/LTSC Support End",
    "Notes", "Recommendation", "Upgrade", "Replace",
    "Primary Alternative", "Secondary Alternative"
]

DB_COLUMNS = [
    "Database", "Version", "Type",
    "Mainstream / Premier End", "Extended Support End",
    "Status", "Notes", "Recommendation",
    "Upgrade", "Replace", "Primary Alternative", "Secondary Alternative"
]

OS_FETCH_PROMPT = """You are a senior IT lifecycle analyst. Search the internet for comprehensive and current lifecycle data for the {family} operating system family.

Hint: {hint}
Search query: {query}

Today's date: {today}

After searching, return ONLY a valid JSON array (no markdown, no extra text) listing ALL versions you find.
Be exhaustive — include every version and sub-version available.

Each element must use EXACTLY these field names:
[
  {{
    "OS Version": "full descriptive name e.g. Windows 11 24H2",
    "Availability Date": "YYYY-MM-DD or empty string",
    "Security/Standard Support End": "YYYY-MM-DD or empty string",
    "Mainstream/Full Support End": "YYYY-MM-DD or text like 'Ended' or 'Active' or 'Rolling'",
    "Extended/LTSC Support End": "YYYY-MM-DD or empty string",
    "Notes": "codename, edition notes, or key lifecycle notes",
    "Recommendation": "",
    "Upgrade": "Y if upgrade strongly recommended, else N",
    "Replace": "Y if migration to a different OS recommended, else N",
    "Primary Alternative": "best upgrade or replacement target if applicable",
    "Secondary Alternative": "secondary option or empty string"
  }}
]

Output ONLY the JSON array starting with [ and ending with ]."""

DB_FETCH_PROMPT = """You are a senior database architect. Search the internet for comprehensive and current lifecycle data for {family} database versions.

Hint: {hint}
Search query: {query}

Today's date: {today}

Classify Status as:
- "End of Life" — all vendor support has ended as of today
- "Expiring Soon" — support ends within the next 12 months from today
- "Supported" — currently in active vendor support window
- "Future" — not yet generally available

After searching, return ONLY a valid JSON array (no markdown, no extra text) listing ALL versions found.

Each element must use EXACTLY these field names:
[
  {{
    "Database": "vendor/product name e.g. SQL Server",
    "Version": "version string e.g. 2022, 8.4 LTS, 19c",
    "Type": "Relational | Document (NoSQL) | In-Memory | Time-Series | Graph | Search | Columnar | Cloud-Managed | Multi-Model",
    "Mainstream / Premier End": "YYYY-MM-DD or TBD or empty string",
    "Extended Support End": "YYYY-MM-DD or TBD or empty string",
    "Status": "Supported | End of Life | Expiring Soon | Future",
    "Notes": "edition notes or key lifecycle notes",
    "Recommendation": "",
    "Upgrade": "Y if in-place upgrade strongly recommended, else N",
    "Replace": "Y if migration to a different product recommended, else N",
    "Primary Alternative": "recommended target version or product",
    "Secondary Alternative": "secondary option or empty string"
  }}
]

Output ONLY the JSON array starting with [ and ending with ]."""


class OSDataAgent:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model  = "claude-haiku-4-5-20251001"
        self.today  = datetime.now().strftime("%d %B %Y")

    # ── Fetch ALL OS data from web ────────────────────────────────────────────
    def fetch_all_os_data(self, progress_callback=None) -> pd.DataFrame:
        all_rows = []
        total = len(OS_SEARCH_TARGETS)

        for idx, target in enumerate(OS_SEARCH_TARGETS):
            if progress_callback:
                progress_callback(
                    idx / total,
                    f"🔍 Fetching OS data: {target['family']}  ({idx+1}/{total})"
                )
            rows = self._fetch_family(target, kind="OS")
            all_rows.extend(rows)
            if progress_callback:
                progress_callback(
                    (idx + 1) / total,
                    f"✅ {target['family']}: {len(rows)} versions  |  running total: {len(all_rows)}"
                )

        if not all_rows:
            return pd.DataFrame(columns=OS_COLUMNS)

        df = pd.DataFrame(all_rows)
        for col in OS_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[OS_COLUMNS]
        df = df[~df["OS Version"].str.startswith("[Fetch error", na=False)]
        df = df.drop_duplicates(subset=["OS Version"]).reset_index(drop=True)
        return df

    # ── Fetch ALL DB data from web ────────────────────────────────────────────
    def fetch_all_db_data(self, progress_callback=None) -> pd.DataFrame:
        all_rows = []
        total = len(DB_SEARCH_TARGETS)

        for idx, target in enumerate(DB_SEARCH_TARGETS):
            if progress_callback:
                progress_callback(
                    idx / total,
                    f"🔍 Fetching DB data: {target['family']}  ({idx+1}/{total})"
                )
            rows = self._fetch_family(target, kind="DB")
            all_rows.extend(rows)
            if progress_callback:
                progress_callback(
                    (idx + 1) / total,
                    f"✅ {target['family']}: {len(rows)} versions  |  running total: {len(all_rows)}"
                )

        if not all_rows:
            return pd.DataFrame(columns=DB_COLUMNS)

        df = pd.DataFrame(all_rows)
        for col in DB_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[DB_COLUMNS]
        df = df.drop_duplicates(subset=["Database", "Version"]).reset_index(drop=True)
        return df

    # ── Internal fetcher ──────────────────────────────────────────────────────
    def _fetch_family(self, target: dict, kind: str) -> list:
        if kind == "OS":
            prompt = OS_FETCH_PROMPT.format(
                family=target["family"],
                hint=target["hint"],
                query=target["query"],
                today=self.today
            )
            fallback_cols = OS_COLUMNS
        else:
            prompt = DB_FETCH_PROMPT.format(
                family=target["family"],
                hint=target["hint"],
                query=target["query"],
                today=self.today
            )
            fallback_cols = DB_COLUMNS

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": prompt}]
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            return self._parse_json_array(text)

        except Exception as e:
            # Return a flagged error row so UI can show it
            row = {col: "" for col in fallback_cols}
            if kind == "OS":
                row["OS Version"] = f"[Fetch error: {target['family']}]"
                row["Notes"] = str(e)[:120]
            else:
                row["Database"] = target["family"]
                row["Version"]  = "Error"
                row["Notes"]    = str(e)[:120]
            return [row]

    def _parse_json_array(self, text: str) -> list:
        text = text.strip()
        for fence in ("```json", "```"):
            if fence in text:
                parts = text.split(fence, 1)
                text = parts[1]
                if "```" in text:
                    text = text.split("```", 1)[0]
                text = text.strip()
                break
        start = text.find("[")
        end   = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]
        try:
            data = json.loads(text)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    # ── Change detection ──────────────────────────────────────────────────────
    def detect_os_changes(self, old_df: pd.DataFrame, new_df: pd.DataFrame) -> list:
        return _diff_dataframes(
            old_df, new_df,
            key_cols=["OS Version"],
            watch_cols=["Mainstream/Full Support End", "Extended/LTSC Support End",
                        "Security/Standard Support End"]
        )

    def detect_db_changes(self, old_df: pd.DataFrame, new_df: pd.DataFrame) -> list:
        return _diff_dataframes(
            old_df, new_df,
            key_cols=["Database", "Version"],
            watch_cols=["Mainstream / Premier End", "Extended Support End", "Status"]
        )


def _diff_dataframes(old_df, new_df, key_cols, watch_cols) -> list:
    changes = []
    if old_df is None or old_df.empty:
        return changes

    def make_key(row):
        return " | ".join(str(row.get(c, "")) for c in key_cols)

    old_map = {make_key(r): dict(r) for _, r in old_df.iterrows()}
    new_map = {make_key(r): dict(r) for _, r in new_df.iterrows()}

    for k, new_row in new_map.items():
        if k.startswith("[Fetch error"):
            continue
        if k not in old_map:
            changes.append(f"➕ NEW ENTRY: {k}")
        else:
            for col in watch_cols:
                ov = str(old_map[k].get(col, "")).strip()
                nv = str(new_row.get(col, "")).strip()
                if ov != nv and nv not in ("", "nan"):
                    changes.append(f"📅 CHANGED — {k} | {col}: '{ov}' → '{nv}'")

    for k in old_map:
        if k not in new_map:
            changes.append(f"➖ REMOVED: {k}")

    return changes
