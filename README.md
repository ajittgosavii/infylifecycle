# INFY Migration Version Lifecycle Tracker

Multi-Agent Streamlit application for tracking OS and Database version lifecycle dates,
powered by **Claude AI** (Anthropic). Built for Infosys Enterprise Architecture teams.

---

## 🤖 Three Agents

| Agent | Role | Technology |
|-------|------|-----------|
| **Agent 1** | Fetches and verifies OS & DB lifecycle dates from the internet | Claude AI + web_search tool |
| **Agent 2** | Generates expert recommendations for every OS and DB entry | Claude claude-opus-4-20250514 |
| **Agent 3** | Bi-weekly refresh monitor — seeks user permission before re-running | Streamlit session state timer |

---

## 📁 Project Structure

```
infy_tracker/
├── app.py                   # Main Streamlit application
├── baseline_data.py         # Embedded OS (81 rows) + DB (44 rows) data
├── requirements.txt         # Python dependencies
├── agents/
│   ├── agent_os.py          # Agent 1: Web search data fetcher
│   ├── agent_db.py          # Agent 2: AI recommendation engine
│   └── agent_refresh.py     # Agent 3: Bi-weekly refresh monitor
├── utils/
│   └── excel_export.py      # openpyxl Excel export with formatting
└── .streamlit/
    └── secrets.toml         # API key (do NOT commit to GitHub)
```

---

## 🚀 Deploy to Streamlit Cloud (Free)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: INFY Version Tracker"
git remote add origin https://github.com/YOUR_USERNAME/infy-version-tracker.git
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app** → select your GitHub repo
3. Set **Main file path** to `app.py`
4. Click **Advanced settings → Secrets** and paste:
   ```
   ANTHROPIC_API_KEY = "sk-ant-your-api-key-here"
   ```
5. Click **Deploy** — live in ~2 minutes!

---

## 💻 Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Enter your Anthropic API key in the sidebar when prompted.

---

## 📥 Excel Download

The **Download Excel** button exports a formatted `.xlsx` file containing:
- **Sheet 1: OS Versions** — all OS entries with recommendations, colour-coded
- **Sheet 2: DB Versions** — all DB entries with status highlighting + recommendations
- **Sheet 3: Summary** — generation metadata and agent descriptions

---

## 📋 Data Coverage

**OS Versions (81 entries):**
Windows 10/11 Client, Windows Server 2012–2025, RHEL 5–10, Ubuntu 14.04–24.04 LTS,
SLES 11–16, Debian 8–13, Rocky/AlmaLinux 8–10, Oracle Linux 7–10,
Solaris 10/11, AIX 6.1–7.3, HP-UX 11i, FreeBSD 12–15, macOS 13–26, OpenVMS, Tru64

**DB Versions (44 entries):**
SQL Server 2012–2025, Oracle DB 11g–23ai, PostgreSQL 13–18,
MySQL 5.7–9.7 LTS, MariaDB 10.4–11.8, MongoDB 4.4–8,
Redis 6.2–8, IBM Db2 10.5–11.5

---

*Infosys Enterprise Architecture · Powered by Claude AI (Anthropic)*
