# INFY Migration Version Lifecycle Tracker

Multi-Agent Streamlit app powered by **Claude AI** (Anthropic).
**All data is fetched live from the internet — there is no hardcoded baseline.**

---

## 🤖 Three Agents

| Agent | Role | Searches |
|-------|------|----------|
| **Agent 1** | Fetches ALL OS & DB lifecycle data live from the web | ~38 Claude AI web searches |
| **Agent 2** | Generates expert migration recommendations per row | Claude claude-opus-4-20250514 |
| **Agent 3** | Bi-weekly refresh monitor with user permission dialog | Session state timer |

---

## 📋 Coverage

**OS Families (18 search targets):**
Windows 10/11 Client, Windows Server 2003–2025, RHEL 4–10, Ubuntu 14.04–25.04,
SLES 11–16 SP7, Debian 8–13, CentOS 6–Stream 10, Rocky/AlmaLinux 8–10,
Oracle Linux 6–10, openSUSE/Fedora, macOS 10.14–26, Solaris 10/11,
AIX 6.1–7.3 TL, HP-UX 11i, FreeBSD 11–15, OpenVMS/Tru64, Android, iOS/iPadOS

**DB Products (20 search targets):**
SQL Server 2008–2025, Oracle DB 10g–23ai, PostgreSQL 9.6–18,
MySQL 5.6–9.7 LTS, MariaDB 10.3–11.8, MongoDB 3.6–8.0,
Redis 5.0–8.0, IBM Db2 9.7–11.5, Cassandra 3.x–5.x,
Elasticsearch 6–8, SAP HANA, SAP/Sybase ASE, Teradata/Vantage,
Amazon Aurora, Amazon RDS, CouchDB/Couchbase, Neo4j 3–5,
InfluxDB/TimescaleDB, Snowflake/Databricks, Azure SQL/Cosmos DB

---

## 🚀 Deploy to Streamlit Cloud

```bash
# 1. Push to GitHub
git init && git add . && git commit -m "INFY Version Tracker"
git remote add origin https://github.com/YOUR_USER/infy-version-tracker.git
git push -u origin main

# 2. Go to share.streamlit.io → New App → select repo → app.py
# 3. Settings → Secrets → add:
#    ANTHROPIC_API_KEY = "sk-ant-your-key"
# 4. Deploy — live in ~2 minutes
```

## 💻 Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Project Structure

```
infy_tracker/
├── app.py                   ← Main Streamlit UI
├── requirements.txt
├── agents/
│   ├── agent_os.py          ← Agent 1: Live web data fetcher (no baseline)
│   ├── agent_db.py          ← Agent 2: AI recommendation engine
│   └── agent_refresh.py     ← Agent 3: Bi-weekly refresh monitor
├── utils/
│   └── excel_export.py      ← openpyxl formatted Excel export
└── .streamlit/
    └── secrets.toml         ← API key (do NOT commit to GitHub)
```

---
*Infosys Enterprise Architecture · Powered by Claude AI (Anthropic)*
