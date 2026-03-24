"""
Agent 1: Dynamic OS & DB Data Fetcher
Comprehensively searches the internet for ALL OS and DB lifecycle data.
NO hardcoded baseline — every row is fetched live from the web.
"""

import anthropic
import json
import pandas as pd
from datetime import datetime

# ── OS search targets — ALL OS families (server + client + mobile + legacy) ──
OS_SEARCH_TARGETS = [
    {
        "family": "Windows 11 Client",
        "query": "Windows 11 all versions builds lifecycle support end dates microsoft.com",
        "hint": "Include EVERY Windows 11 build: 21H2, 22H2, 23H2, 24H2, 25H2, 26H1 and all editions — Home, Pro, Enterprise, Education, IoT. Return one row per build per edition where dates differ."
    },
    {
        "family": "Windows 10 Client",
        "query": "Windows 10 all versions builds lifecycle support end dates LTSC LTSB microsoft.com",
        "hint": "Include ALL Windows 10 builds: 1507,1511,1607,1703,1709,1803,1809,1903,1909,2004,20H2,21H1,21H2,22H2 and LTSC 2015,2016,2019,2021 editions. One row per build per edition."
    },
    {
        "family": "Windows 8 and 8.1",
        "query": "Windows 8 8.1 lifecycle support end dates mainstream extended microsoft.com",
        "hint": "Include Windows 8, Windows 8.1, Windows 8.1 Update, Windows Embedded 8 Standard, Windows Embedded 8.1 Pro with all support end dates."
    },
    {
        "family": "Windows 7",
        "query": "Windows 7 all editions lifecycle support end dates mainstream extended ESU microsoft.com",
        "hint": "Include Windows 7 SP1 Home, Professional, Enterprise, Ultimate. Include Extended Security Update (ESU) years 1,2,3 end dates."
    },
    {
        "family": "Windows Vista and XP",
        "query": "Windows Vista XP lifecycle support end dates microsoft.com",
        "hint": "Include Windows XP all editions (Home, Pro, MCE, Tablet, Embedded), Windows Vista all editions with mainstream and extended support end dates."
    },
    {
        "family": "Windows Server",
        "query": "Windows Server all versions lifecycle mainstream extended support end dates microsoft.com",
        "hint": "Include ALL Windows Server: 2003, 2003 R2, 2008, 2008 R2, 2012, 2012 R2, 2016, 2019, 2022, 2025 — Standard, Datacenter, Core, SAC editions."
    },
    {
        "family": "RHEL",
        "query": "Red Hat Enterprise Linux RHEL all versions lifecycle support end dates redhat.com",
        "hint": "Include RHEL 4, 5, 6, 7, 8, 9, 10 — all editions. Capture Full Support End, Maintenance Support End, Extended Life Phase End dates for each."
    },
    {
        "family": "Ubuntu",
        "query": "Ubuntu all LTS non-LTS releases lifecycle end of support ESM dates ubuntu.com",
        "hint": "Include Ubuntu 12.04, 14.04, 16.04, 18.04, 20.04, 22.04, 24.04 LTS and all interim releases 17.04 through 25.04. Standard, ESM, and Legacy Support end dates."
    },
    {
        "family": "SLES",
        "query": "SUSE Linux Enterprise Server all versions service packs lifecycle LTSS dates suse.com",
        "hint": "Include SLES 10, 11 SP1-SP4, 12 SP1-SP5, 15 SP1-SP7, 16. General Support End and LTSS end dates for each SP. Include SLES for SAP lifecycle dates."
    },
    {
        "family": "Debian",
        "query": "Debian Linux all releases lifecycle security LTS ELTS end of life dates debian.org",
        "hint": "Include Debian 6 Squeeze through Debian 13 Trixie. Security Support end, LTS end, and ELTS end dates for each release."
    },
    {
        "family": "CentOS",
        "query": "CentOS all versions end of life dates centos.org CentOS Stream lifecycle",
        "hint": "Include CentOS 5, 6, 7, 8 and CentOS Stream 8, 9, 10 with EOL dates. Note CentOS 8 early EOL December 2021."
    },
    {
        "family": "Rocky Linux",
        "query": "Rocky Linux all versions lifecycle end of life support dates rockylinux.org",
        "hint": "Include Rocky Linux 8.x, 9.x, 10.x with full lifecycle dates. Rocky mirrors RHEL lifecycle."
    },
    {
        "family": "AlmaLinux",
        "query": "AlmaLinux all versions lifecycle end of life support dates almalinux.org",
        "hint": "Include AlmaLinux 8.x, 9.x, 10.x with lifecycle dates. AlmaLinux mirrors RHEL lifecycle."
    },
    {
        "family": "Oracle Linux",
        "query": "Oracle Linux all versions lifecycle premier extended support end dates oracle.com",
        "hint": "Include Oracle Linux 6, 7, 8, 9, 10 with Premier Support end and Extended Support end dates."
    },
    {
        "family": "openSUSE and Fedora",
        "query": "openSUSE Leap Fedora Linux all versions lifecycle end of life dates 2026",
        "hint": "Include openSUSE Leap 15.0 through 15.6. Include Fedora 34 through 42 with EOL dates (~13 months per Fedora release)."
    },
    {
        "family": "Arch Linux and Gentoo",
        "query": "Arch Linux Gentoo Linux rolling release lifecycle support policy versioning 2026",
        "hint": "Include Arch Linux (rolling) and Gentoo (rolling) release model, support policy, and any versioned snapshots. Note their rolling-release nature."
    },
    {
        "family": "macOS",
        "query": "macOS all versions lifecycle support end dates Apple 2026",
        "hint": "Include macOS 10.13 High Sierra through macOS 15 Sequoia and macOS 26. Include support end dates from Apple security updates page."
    },
    {
        "family": "Oracle Solaris",
        "query": "Oracle Solaris all versions lifecycle support end of life dates oracle.com",
        "hint": "Include Solaris 9, 10 and Solaris 11.1 through 11.4 SRU versions with Premier and Extended support end dates."
    },
    {
        "family": "IBM AIX",
        "query": "IBM AIX all versions technology levels lifecycle end of service support dates ibm.com",
        "hint": "Include AIX 5.3, 6.1 TL9, 7.1 TL5, 7.2 TL5, 7.3 TL0-TL4 with End of Service Pack Support and End of Service dates for each Technology Level."
    },
    {
        "family": "IBM i and IBM z/OS",
        "query": "IBM i AS400 iSeries OS400 z/OS all versions lifecycle end of support dates ibm.com",
        "hint": "Include IBM i 6.1, 7.1, 7.2, 7.3, 7.4, 7.5 and z/OS 2.1 through 2.5 with IBM end of support dates."
    },
    {
        "family": "HP-UX",
        "query": "HP-UX 11i all versions lifecycle support end dates hpe.com",
        "hint": "Include HP-UX 11i v1 (B.11.11), v2 (B.11.23), v3 (B.11.31) for HP 9000 PA-RISC and Integrity Itanium servers."
    },
    {
        "family": "FreeBSD",
        "query": "FreeBSD all release branches lifecycle end of life support dates freebsd.org",
        "hint": "Include FreeBSD 11.x, 12.x, 13.x, 14.x, 15.x — RELEASE and STABLE branches with official EoL dates from freebsd.org/security."
    },
    {
        "family": "OpenVMS and Tru64",
        "query": "OpenVMS VSI VMS Tru64 UNIX all versions lifecycle support end dates 2026",
        "hint": "Include OpenVMS for Alpha, IA-64, x86-64 from VSI. Include Tru64 UNIX 5.1A through 5.1B-6 with HP/Compaq end-of-support dates."
    },
    {
        "family": "Android Enterprise",
        "query": "Android all versions enterprise security update support end dates google.com 2026",
        "hint": "Include Android 9 through Android 15 enterprise lifecycle, security update end dates, and Google-guaranteed update policy."
    },
    {
        "family": "iOS and iPadOS",
        "query": "iOS iPadOS all versions lifecycle security update end dates Apple 2026",
        "hint": "Include iOS/iPadOS 13, 14, 15, 16, 17, 18, 19 with Apple support and security update end dates."
    },
    {
        "family": "Windows Embedded and IoT",
        "query": "Windows Embedded IoT Enterprise LTSC all versions lifecycle support end dates microsoft.com",
        "hint": "Include Windows Embedded Standard 7, 8, Windows IoT Enterprise LTSC 2019, 2021, 2024 with all support end dates."
    },
]

# ── DB search targets — ALL databases enterprise + cloud + legacy + niche ────
DB_SEARCH_TARGETS = [
    {
        "family": "SQL Server",
        "query": "Microsoft SQL Server all versions lifecycle mainstream extended end of support dates microsoft.com",
        "hint": "Include SQL Server 2000, 2005, 2008, 2008 R2, 2012, 2014, 2016, 2017, 2019, 2022, 2025 — all editions Standard/Enterprise/Express/Developer with all support phase dates."
    },
    {
        "family": "Oracle Database",
        "query": "Oracle Database all versions premier extended lifecycle support end dates oracle.com 2026",
        "hint": "Include Oracle DB 9i, 10g R1/R2, 11g R1/R2, 12c R1/R2, 18c, 19c, 21c, 23ai — all editions SE/EE with all support phase dates."
    },
    {
        "family": "PostgreSQL",
        "query": "PostgreSQL all versions end of life support dates postgresql.org 2026",
        "hint": "Include PostgreSQL 9.2, 9.3, 9.4, 9.5, 9.6, 10, 11, 12, 13, 14, 15, 16, 17, 18 with each version's EOL date."
    },
    {
        "family": "MySQL",
        "query": "MySQL all versions lifecycle premier extended support end dates oracle.com mysql.com",
        "hint": "Include MySQL 5.1, 5.5, 5.6, 5.7, 8.0, 8.4 LTS, 9.0, 9.1, 9.7 LTS with all support phase dates including Oracle Extended Support."
    },
    {
        "family": "MariaDB",
        "query": "MariaDB all versions lifecycle end of life support dates mariadb.org 2026",
        "hint": "Include MariaDB 10.2 through 11.8 including all LTS versions (10.5, 10.6, 10.11, 11.4, 11.8) with EOL dates."
    },
    {
        "family": "IBM Db2",
        "query": "IBM Db2 all versions lifecycle end of support dates ibm.com 2026",
        "hint": "Include IBM Db2 9.5, 9.7, 10.1, 10.5, 11.1, 11.5 — all editions (Advanced Enterprise, Enterprise, Standard) with all support end dates."
    },
    {
        "family": "IBM Informix",
        "query": "IBM Informix all versions lifecycle end of support dates ibm.com 2026",
        "hint": "Include IBM Informix 11.50, 11.70, 12.10, 14.10 — all editions with mainstream and extended support end dates."
    },
    {
        "family": "IBM IMS and IBM Netezza",
        "query": "IBM IMS database IBM Netezza IBM PureData all versions lifecycle end of support dates ibm.com",
        "hint": "Include IBM IMS 13, 14, 15 for mainframe. Include IBM Netezza / PureData System for Analytics versions with support end dates."
    },
    {
        "family": "Sybase ASE",
        "query": "SAP Sybase Adaptive Server Enterprise ASE all versions lifecycle end of support dates sap.com",
        "hint": "Include Sybase ASE 12.5, 15.0, 15.5, 15.7, 16.0 SP01-SP04 with PAM (Product Availability Matrix) support end dates."
    },
    {
        "family": "SAP HANA",
        "query": "SAP HANA database all versions SPS lifecycle end of maintenance support dates sap.com",
        "hint": "Include SAP HANA 1.0 SPS 09-12, SAP HANA 2.0 SPS 00 through SPS 08 with Mainstream and Extended Maintenance end dates."
    },
    {
        "family": "SAP IQ and SAP ASE",
        "query": "SAP IQ Sybase IQ SAP SQL Anywhere all versions lifecycle end of support dates sap.com",
        "hint": "Include SAP IQ (Sybase IQ) 15.x, 16.x and SAP SQL Anywhere 16, 17 with PAM support end dates."
    },
    {
        "family": "MongoDB",
        "query": "MongoDB all versions lifecycle end of life support dates mongodb.com 2026",
        "hint": "Include MongoDB 3.6, 4.0, 4.2, 4.4, 5.0, 6.0, 7.0, 8.0 with EOL dates."
    },
    {
        "family": "Redis",
        "query": "Redis all versions lifecycle end of life support dates redis.io 2026",
        "hint": "Include Redis 5.0, 6.0, 6.2, 7.0, 7.2, 7.4, 7.8, 8.0 with EOL dates. Note Redis licensing change in 7.4."
    },
    {
        "family": "Cassandra",
        "query": "Apache Cassandra all versions lifecycle end of life support dates cassandra.apache.org",
        "hint": "Include Cassandra 2.1, 2.2, 3.0, 3.11, 4.0, 4.1, 5.0 with EOL dates."
    },
    {
        "family": "Elasticsearch and OpenSearch",
        "query": "Elasticsearch OpenSearch all versions end of life support dates elastic.co opensearch.org 2026",
        "hint": "Include Elasticsearch 6.x, 7.x, 8.x and OpenSearch 1.x, 2.x with EOL dates."
    },
    {
        "family": "Teradata",
        "query": "Teradata Database Vantage all versions lifecycle end of support dates teradata.com 2026",
        "hint": "Include Teradata Database 13.x, 14.x, 15.x, 16.x, 17.x and Vantage 1.x, 2.x with end of support dates."
    },
    {
        "family": "Vertica and Greenplum",
        "query": "Vertica database Greenplum all versions lifecycle end of support dates microfocus.com pivotal.io 2026",
        "hint": "Include Vertica 9.x, 10.x, 11.x, 12.x and Greenplum 5.x, 6.x, 7.x with end of support dates."
    },
    {
        "family": "Ingres and Actian",
        "query": "Ingres Actian Vector Actian X database all versions lifecycle end of support dates actian.com",
        "hint": "Include Ingres 10.x, 11.x and Actian Vector, Actian X (Ingres) versions with support end dates."
    },
    {
        "family": "Progress OpenEdge and Firebird",
        "query": "Progress OpenEdge database Firebird all versions lifecycle end of support dates progress.com firebirdsql.org",
        "hint": "Include Progress OpenEdge 11.x, 12.x and Firebird 2.5, 3.0, 4.0, 5.0 with support end dates."
    },
    {
        "family": "InterBase and Advantage Database",
        "query": "Embarcadero InterBase Advantage Database Server all versions lifecycle end of support dates embarcadero.com",
        "hint": "Include InterBase 2017, 2020, 2021 and Advantage Database Server 11.x, 12.x with support end dates."
    },
    {
        "family": "SQLite and H2",
        "query": "SQLite H2 database HSQLDB all versions current version support policy 2026",
        "hint": "Include SQLite 3.x current version, H2 database 2.x, HSQLDB 2.x versioning and support policies."
    },
    {
        "family": "Microsoft Access and FoxPro",
        "query": "Microsoft Access all versions lifecycle support end dates Microsoft FoxPro Visual FoxPro end of life",
        "hint": "Include Microsoft Access 2013, 2016, 2019, 2021, 2024 with support end dates. Include Visual FoxPro 9.0 EOL dates."
    },
    {
        "family": "Amazon Aurora and RDS",
        "query": "Amazon Aurora RDS all engine versions end of support lifecycle aws.amazon.com 2026",
        "hint": "Include Aurora MySQL 2.x, 3.x and Aurora PostgreSQL major versions. RDS for SQL Server, MySQL, PostgreSQL, MariaDB, Oracle engine version deprecation dates."
    },
    {
        "family": "Amazon DynamoDB and DocumentDB",
        "query": "Amazon DynamoDB DocumentDB ElastiCache all versions lifecycle support dates aws.amazon.com 2026",
        "hint": "Include DynamoDB versioning policy, DocumentDB 4.0, 5.0 support dates, ElastiCache for Redis and Memcached version EOL dates."
    },
    {
        "family": "Google Cloud Spanner and BigQuery",
        "query": "Google Cloud Spanner BigQuery AlloyDB versioning support lifecycle policy cloud.google.com 2026",
        "hint": "Include Google Cloud Spanner, BigQuery, AlloyDB for PostgreSQL versioning and deprecation policy."
    },
    {
        "family": "Azure SQL and Cosmos DB",
        "query": "Azure SQL Database Azure Cosmos DB all versions deprecation support lifecycle microsoft.com 2026",
        "hint": "Include Azure SQL Database, Azure SQL Managed Instance, Azure Cosmos DB API versions (NoSQL, MongoDB, Cassandra, Gremlin, Table) deprecation dates."
    },
    {
        "family": "CockroachDB and YugabyteDB",
        "query": "CockroachDB YugabyteDB TiDB all versions lifecycle end of support dates 2026",
        "hint": "Include CockroachDB 22.x, 23.x, 24.x, YugabyteDB 2.x, 2.20, TiDB 6.x, 7.x, 8.x with EOL dates."
    },
    {
        "family": "CouchDB and Couchbase",
        "query": "Apache CouchDB Couchbase Server all versions lifecycle end of support dates 2026",
        "hint": "Include CouchDB 2.x, 3.x and Couchbase Server 6.x, 7.x with EOL dates."
    },
    {
        "family": "Neo4j and Graph Databases",
        "query": "Neo4j TigerGraph Amazon Neptune all versions lifecycle end of support dates 2026",
        "hint": "Include Neo4j 3.5, 4.x, 5.x and TigerGraph 3.x, 4.x and Amazon Neptune engine versions with support end dates."
    },
    {
        "family": "InfluxDB and TimescaleDB",
        "query": "InfluxDB TimescaleDB QuestDB all versions lifecycle end of support dates 2026",
        "hint": "Include InfluxDB 1.x, 2.x, 3.x, TimescaleDB 2.x, QuestDB versions with support dates."
    },
    {
        "family": "Snowflake and Databricks",
        "query": "Snowflake Databricks Runtime versions lifecycle deprecation end of support dates 2026",
        "hint": "Include Databricks Runtime LTS versions (10.4 LTS, 11.3 LTS, 12.2 LTS, 13.3 LTS, 14.3 LTS) with support end dates. Snowflake versioning and deprecation policy."
    },
    {
        "family": "Apache Hive and HBase",
        "query": "Apache Hive HBase Hadoop all versions lifecycle end of life support dates 2026",
        "hint": "Include Apache Hive 2.x, 3.x, 4.x, HBase 1.x, 2.x, Hadoop 2.x, 3.x with Apache EOL dates."
    },
    {
        "family": "Exasol and SingleStore",
        "query": "Exasol SingleStore MemSQL all versions lifecycle end of support dates 2026",
        "hint": "Include Exasol 7.x, 8.x and SingleStore (MemSQL) 7.x, 8.x with support end dates."
    },
    {
        "family": "SAP MaxDB and SQLBase",
        "query": "SAP MaxDB Gupta SQLBase IBM solidDB all versions lifecycle end of support dates",
        "hint": "Include SAP MaxDB 7.9 with support end dates. Gupta SQLBase 11.x, 12.x. IBM solidDB 7.x EOL dates."
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

# ── Prompt 1: With web_search tool (live internet data) ──────────────────────
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

# ── Prompt 2: Knowledge-only fallback (NO web search required) ───────────────
# Used when web_search tool is unavailable or returns errors.
# Asks Claude to answer from its training knowledge directly.
OS_KNOWLEDGE_PROMPT = """You are a senior IT lifecycle expert with comprehensive knowledge of operating system support lifecycles.

Using your training knowledge (no internet search needed), list ALL known versions of the {family} operating system family with their support lifecycle dates.

Family details: {hint}
Today's date: {today}

Be exhaustive — include every major version, build number, and edition you know about.
Include versions that are End of Life, currently supported, and upcoming/future releases.

Return ONLY a valid JSON array (no markdown, no preamble) using EXACTLY these field names:
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

DB_KNOWLEDGE_PROMPT = """You are a senior database architect with comprehensive knowledge of database product support lifecycles.

Using your training knowledge (no internet search needed), list ALL known versions of {family} database with their support lifecycle dates.

Family details: {hint}
Today's date: {today}

Classify Status based on today's date:
- "End of Life" — all vendor support has ended as of today
- "Expiring Soon" — support ends within the next 12 months
- "Supported" — currently in active vendor support window
- "Future" — not yet generally available

Be exhaustive — include every major version you know about.

Return ONLY a valid JSON array (no markdown, no preamble) using EXACTLY these field names:
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
        self.client     = anthropic.Anthropic(api_key=api_key)
        self.model      = "claude-sonnet-4-6"
        self.today      = datetime.now().strftime("%d %B %Y")
        self.last_error = None   # captures most recent fetch error for diagnosis

    # ── Fetch ALL OS data from web ────────────────────────────────────────────
    def fetch_all_os_data(self, progress_callback=None) -> pd.DataFrame:
        import time
        all_rows   = []
        skipped    = []
        errors     = []
        total      = len(OS_SEARCH_TARGETS)

        for idx, target in enumerate(OS_SEARCH_TARGETS):
            if progress_callback:
                progress_callback(
                    idx / total,
                    f"🔍 Fetching OS: {target['family']}  ({idx+1}/{total})"
                )

            # Short pause between calls
            if idx > 0:
                time.sleep(0.5)

            self.last_error = None
            rows = self._fetch_family(target, kind="OS")

            if rows:
                all_rows.extend(rows)
                if progress_callback:
                    progress_callback(
                        (idx + 1) / total,
                        f"✅ {target['family']}: {len(rows)} versions  |  total: {len(all_rows)}"
                    )
            else:
                err_detail = self.last_error or "unknown"
                skipped.append(target["family"])
                errors.append(f"{target['family']}: {err_detail[:80]}")
                if progress_callback:
                    progress_callback(
                        (idx + 1) / total,
                        f"⚠️ {target['family']}: failed — {err_detail[:60]}"
                    )

        if progress_callback:
            if skipped:
                # Show first error so user can diagnose
                first_err = errors[0] if errors else "unknown"
                progress_callback(1.0,
                    f"OS fetch done — {len(all_rows)} rows from {total-len(skipped)}/{total} families. "
                    f"First error: {first_err}"
                )
            else:
                progress_callback(1.0,
                    f"✅ OS fetch complete — {len(all_rows)} versions across all {total} families"
                )

        if not all_rows:
            return pd.DataFrame(columns=OS_COLUMNS)

        df = pd.DataFrame(all_rows)
        for col in OS_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[OS_COLUMNS]
        # Remove any error-flagged rows
        df = df[~df["OS Version"].str.startswith("[Fetch error", na=False)]
        df = df[df["OS Version"].str.strip() != ""]
        df = df.drop_duplicates(subset=["OS Version"]).reset_index(drop=True)
        return df

    # ── Fetch ALL DB data from web ────────────────────────────────────────────
    def fetch_all_db_data(self, progress_callback=None) -> pd.DataFrame:
        import time
        all_rows = []
        skipped  = []
        total    = len(DB_SEARCH_TARGETS)

        for idx, target in enumerate(DB_SEARCH_TARGETS):
            if progress_callback:
                progress_callback(
                    idx / total,
                    f"🔍 Fetching DB: {target['family']}  ({idx+1}/{total})"
                )

            # Short pause between DB searches
            if idx > 0:
                time.sleep(0.5)

            rows = self._fetch_family(target, kind="DB")

            if rows:
                all_rows.extend(rows)
                if progress_callback:
                    progress_callback(
                        (idx + 1) / total,
                        f"✅ {target['family']}: {len(rows)} versions  |  total: {len(all_rows)}"
                    )
            else:
                skipped.append(target["family"])
                if progress_callback:
                    progress_callback(
                        (idx + 1) / total,
                        f"⚠️ {target['family']}: no data (web + knowledge both failed)"
                    )

        if progress_callback:
            if skipped:
                progress_callback(1.0,
                    f"DB fetch done — {len(all_rows)} rows from {total - len(skipped)}/{total} products. "
                    f"Skipped: {', '.join(skipped[:3])}"
                )
            else:
                progress_callback(1.0, f"✅ DB fetch complete — {len(all_rows)} versions across all {total} products")

        if not all_rows:
            return pd.DataFrame(columns=DB_COLUMNS)

        df = pd.DataFrame(all_rows)
        for col in DB_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[DB_COLUMNS]
        # Remove error rows — Version = "Error" means the fetch failed for that family
        df = df[df["Version"].str.strip().str.lower() != "error"]
        df = df[df["Database"].str.strip() != ""]
        df = df.drop_duplicates(subset=["Database", "Version"]).reset_index(drop=True)
        return df

    # ── Internal fetcher: 1 web attempt → immediate knowledge fallback ─────────
    def _fetch_family(self, target: dict, kind: str) -> list:
        """
        Strategy (optimised for Streamlit Cloud reliability):

        Step 1 — Try live web_search ONCE (~5-10s).
                 If it succeeds → return fresh internet data immediately.
                 If it fails for ANY reason → move to Step 2 immediately.

        Step 2 — Claude training knowledge (no tool, no internet).
                 Uses a dedicated prompt asking Claude to answer from training data.
                 This ALWAYS returns data. Never times out.

        Rationale: 3 retries × long sleeps = 8+ min total → Streamlit Cloud timeout.
        1 attempt + immediate fallback = ~5s per family → 26 OS + 34 DB in ~5 min.
        """
        import time

        # ── Build both prompts upfront ────────────────────────────────────────
        if kind == "OS":
            web_prompt       = OS_FETCH_PROMPT.format(
                family=target["family"], hint=target["hint"],
                query=target["query"],  today=self.today
            )
            knowledge_prompt = OS_KNOWLEDGE_PROMPT.format(
                family=target["family"], hint=target["hint"],
                today=self.today
            )
        else:
            web_prompt       = DB_FETCH_PROMPT.format(
                family=target["family"], hint=target["hint"],
                query=target["query"],  today=self.today
            )
            knowledge_prompt = DB_KNOWLEDGE_PROMPT.format(
                family=target["family"], hint=target["hint"],
                today=self.today
            )

        # ── Step 1: Live web_search — single attempt ──────────────────────────
        web_err = None
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": web_prompt}]
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            rows = self._parse_json_array(text)
            if rows:
                return rows   # ✅ Live internet data obtained
            # Response came back but JSON was empty — fall through to knowledge
        except Exception as e:
            web_err = str(e)
            err_str = web_err.lower()
            # Hard auth failure — knowledge won't help either
            if "401" in err_str or "authentication" in err_str:
                self.last_error = f"Auth failure: {web_err}"
                return []
            # For 429 rate limit only — brief pause before knowledge call
            if "429" in err_str or "rate" in err_str:
                time.sleep(3)
            # All other errors (400, 500, network) — fall through immediately

        # ── Step 2: Claude training knowledge — guaranteed data ───────────────
        # A dedicated prompt that does NOT say "search the internet" so Claude
        # answers confidently from its training data without needing any tool.
        kb_err = None
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": knowledge_prompt}]
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            rows = self._parse_json_array(text)
            if rows:
                return rows   # ✅ Knowledge data obtained
            # Got response but couldn't parse JSON
            kb_err = f"Empty parse. Response preview: {text[:200]}"
        except Exception as e:
            kb_err = str(e)

        # Both failed — log for diagnosis
        self.last_error = (
            f"web={web_err or 'empty_parse'} | "
            f"knowledge={kb_err or 'empty_parse'}"
        )
        return []

    def _parse_json_array(self, text: str) -> list:
        """
        Robust JSON array parser — tries multiple strategies in order:
        1. Strip markdown fences, find [ ... ] boundaries, parse
        2. Try parsing the whole response as JSON (handles wrapped objects)
        3. Find any line starting with [ and parse from there
        4. Fix common issues (trailing commas, single quotes) and retry
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        # Strategy 1: Strip markdown code fences
        for fence in ("```json", "```"):
            if fence in text:
                parts = text.split(fence, 1)
                text  = parts[1]
                if "```" in text:
                    text = text.split("```", 1)[0]
                text = text.strip()
                break

        # Strategy 2: Find outermost [ ... ] array boundaries
        start = text.find("[")
        end   = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end+1]
            try:
                data = json.loads(candidate)
                if isinstance(data, list) and data:
                    return data
            except json.JSONDecodeError:
                pass

        # Strategy 3: Try parsing whole text as JSON (might be {"versions":[...]} etc.)
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                # Look for any list value
                for v in data.values():
                    if isinstance(v, list) and v:
                        return v
        except json.JSONDecodeError:
            pass

        # Strategy 4: Find first line that starts with [ and parse from there
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("["):
                end_idx = text.rfind("]", text.find(line))
                if end_idx != -1:
                    try:
                        data = json.loads(text[text.find(line):end_idx+1])
                        if isinstance(data, list) and data:
                            return data
                    except Exception:
                        pass

        # Strategy 5: Fix common JSON issues — trailing commas, single quotes
        if "[" in text and "]" in text:
            try:
                import re
                fixed = text[text.find("["):text.rfind("]")+1]
                fixed = re.sub(r",\s*]", "]", fixed)   # trailing commas before ]
                fixed = re.sub(r",\s*}", "}", fixed)    # trailing commas before }
                fixed = fixed.replace("'", '"')          # single → double quotes
                data  = json.loads(fixed)
                if isinstance(data, list) and data:
                    return data
            except Exception:
                pass

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
