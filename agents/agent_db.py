"""
Agent 2: AI Recommendation Engine
Generates expert migration recommendations for every OS and DB row
using Claude AI. Operates on whatever data Agent 1 fetched — no hardcoding.
"""

import anthropic
import json
import pandas as pd
from datetime import datetime

CURRENT_DATE = datetime.now().strftime("%B %Y")

OS_SYSTEM = f"""You are a senior enterprise IT architect and OS lifecycle specialist with 25+ years of experience.
Today is {CURRENT_DATE}.

For each OS version entry, generate a concise, actionable 1-2 sentence recommendation based on:
- Its current support status vs today's date
- Upgrade and Replace flags already set
- Primary/Secondary alternatives listed
- Enterprise risk posture (security, compliance, vendor support)

Classification guide:
- All support dates in the past → CRITICAL: Immediate action, security/compliance risk
- Mainstream/Extended end within 6 months → URGENT: Begin migration planning now
- Mainstream/Extended end within 12 months → HIGH PRIORITY: Initiate upgrade project
- Mainstream/Extended end within 24 months → PLAN AHEAD: Start architecture review
- Replace=Y flagged → Include migration target in recommendation
- Rolling/Active release → Note monitoring cadence
- Future release → Note as candidate for adoption planning

Be specific: name exact target versions and dates where possible."""

DB_SYSTEM = f"""You are a senior database architect and migration specialist with 25+ years of experience.
Today is {CURRENT_DATE}.

For each database version entry, generate a concise, actionable 1-2 sentence recommendation based on:
- Status (End of Life / Expiring Soon / Supported / Future)
- Support end dates relative to today
- Replace flag and alternatives listed
- Licensing cost implications (especially Oracle → PostgreSQL migration opportunities)
- Cloud-managed vs on-premise considerations

Classification guide:
- End of Life → CRITICAL: Migrate immediately, cite security/support risk
- Expiring Soon (within 12 months) → URGENT: Migration must start now
- Replace=Y with alternative → Include migration target explicitly
- Oracle versions → Mention OSS alternative (PostgreSQL) for cost reduction
- Cloud-managed versions → Note managed service benefits
- Future → Note as candidate for greenfield deployments

Be specific: name exact target versions and dates."""

BATCH_PROMPT_OS = """Generate recommendations for these OS versions. Return ONLY a valid JSON object mapping each OS Version name to its recommendation text (no markdown fences, no preamble):

{rows}

Expected format:
{{"OS Version Name": "recommendation text", ...}}"""

BATCH_PROMPT_DB = """Generate recommendations for these database versions. Return ONLY a valid JSON object mapping "Database Version" (e.g. "SQL Server 2022") to its recommendation text (no markdown fences, no preamble):

{rows}

Expected format:
{{"Database Version": "recommendation text", ...}}"""


class RecommendationAgent:
    def __init__(self, api_key: str):
        self.client     = anthropic.Anthropic(api_key=api_key)
        self.model      = "claude-sonnet-4-6"
        self.batch_size = 20

    # ── OS recommendations ────────────────────────────────────────────────────
    def generate_os_recommendations(self, df: pd.DataFrame,
                                     progress_callback=None) -> pd.DataFrame:
        df = df.copy()
        rows = df.to_dict("records")
        recs = {}
        total = len(rows)

        for i in range(0, total, self.batch_size):
            batch = rows[i:i + self.batch_size]
            if progress_callback:
                progress_callback(
                    i / total,
                    f"🤖 Agent 2 — OS: rows {i+1}–{min(i+self.batch_size, total)} of {total}"
                )
            batch_recs = self._recommend_batch(batch, kind="OS")
            recs.update(batch_recs)

        for idx, row in df.iterrows():
            key = row["OS Version"]
            if key in recs:
                df.at[idx, "Recommendation"] = recs[key]

        if progress_callback:
            progress_callback(1.0, f"✅ OS recommendations done — {len(df)} rows processed")
        return df

    # ── DB recommendations ────────────────────────────────────────────────────
    def generate_db_recommendations(self, df: pd.DataFrame,
                                     progress_callback=None) -> pd.DataFrame:
        df = df.copy()
        rows = df.to_dict("records")
        recs = {}
        total = len(rows)

        for i in range(0, total, self.batch_size):
            batch = rows[i:i + self.batch_size]
            if progress_callback:
                progress_callback(
                    i / total,
                    f"🤖 Agent 2 — DB: rows {i+1}–{min(i+self.batch_size, total)} of {total}"
                )
            batch_recs = self._recommend_batch(batch, kind="DB")
            recs.update(batch_recs)

        for idx, row in df.iterrows():
            key = f"{row['Database']} {row['Version']}"
            if key in recs:
                df.at[idx, "Recommendation"] = recs[key]

        if progress_callback:
            progress_callback(1.0, f"✅ DB recommendations done — {len(df)} rows processed")
        return df

    # ── Internal batch call ───────────────────────────────────────────────────
    def _recommend_batch(self, batch: list, kind: str) -> dict:
        if kind == "OS":
            rows_text = "\n".join(
                f"- {r.get('OS Version','?')} | Available: {r.get('Availability Date','')} "
                f"| Security End: {r.get('Security/Standard Support End','')} "
                f"| Mainstream End: {r.get('Mainstream/Full Support End','')} "
                f"| Extended End: {r.get('Extended/LTSC Support End','')} "
                f"| Upgrade: {r.get('Upgrade','')} | Replace: {r.get('Replace','')} "
                f"| Primary Alt: {r.get('Primary Alternative','')} "
                f"| Notes: {r.get('Notes','')}"
                for r in batch
            )
            prompt  = BATCH_PROMPT_OS.format(rows=rows_text)
            system  = OS_SYSTEM
            key_fn  = lambda r: r.get("OS Version", "")
        else:
            rows_text = "\n".join(
                f"- {r.get('Database','?')} {r.get('Version','?')} | Type: {r.get('Type','')} "
                f"| Status: {r.get('Status','')} "
                f"| Mainstream End: {r.get('Mainstream / Premier End','')} "
                f"| Extended End: {r.get('Extended Support End','')} "
                f"| Upgrade: {r.get('Upgrade','')} | Replace: {r.get('Replace','')} "
                f"| Primary Alt: {r.get('Primary Alternative','')} "
                f"| Notes: {r.get('Notes','')}"
                for r in batch
            )
            prompt  = BATCH_PROMPT_DB.format(rows=rows_text)
            system  = DB_SYSTEM
            key_fn  = lambda r: f"{r.get('Database','?')} {r.get('Version','?')}"

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            for fence in ("```json", "```"):
                if fence in text:
                    text = text.split(fence, 1)[-1].split("```", 1)[0].strip()
                    break
            return json.loads(text)

        except Exception:
            # Rule-based fallback for entire batch
            return {key_fn(r): self._rule_based(r, kind) for r in batch}

    # ── Rule-based fallback ───────────────────────────────────────────────────
    def _rule_based(self, row: dict, kind: str) -> str:
        today = datetime.now()

        def parse_date(s):
            if not s or not isinstance(s, str):
                return None
            s = s[:10]
            try:
                return datetime.strptime(s, "%Y-%m-%d")
            except Exception:
                return None

        if kind == "OS":
            end_str = row.get("Extended/LTSC Support End") or row.get("Mainstream/Full Support End", "")
            alt     = row.get("Primary Alternative", "")
            replace = row.get("Replace", "N")
            end_dt  = parse_date(end_str)

            if replace == "Y" and alt:
                return f"MIGRATION RECOMMENDED: Plan migration to {alt} for long-term supportability."
            if end_dt:
                days = (end_dt - today).days
                if days < 0:
                    return "CRITICAL: All vendor support has ended. Upgrade immediately to avoid security and compliance risk."
                elif days < 180:
                    return f"URGENT: Support ends {end_str}. Begin upgrade project immediately."
                elif days < 365:
                    return f"HIGH PRIORITY: Support ends {end_str}. Initiate upgrade planning now."
                elif days < 730:
                    return f"PLAN AHEAD: Support ends {end_str}. Start architecture review and upgrade roadmap."
                else:
                    return f"SUPPORTED: No immediate action. Monitor lifecycle through {end_str}."
            return "Review support lifecycle and plan upgrade path accordingly."
        else:
            status  = row.get("Status", "").lower()
            alt     = row.get("Primary Alternative", "")
            ext_end = row.get("Extended Support End", "")
            replace = row.get("Replace", "N")
            db_name = f"{row.get('Database','DB')} {row.get('Version','')}"

            if status == "end of life":
                return f"CRITICAL: {db_name} is End of Life. Migrate{' to ' + alt if alt else ''} immediately — no patches or security fixes available."
            elif status == "expiring soon":
                return f"URGENT: Support ending soon (extended end: {ext_end}). Begin migration{' to ' + alt if alt else ''} immediately."
            elif status == "future":
                return f"MONITOR: {db_name} is not yet released. Track GA timeline for new project adoption."
            elif replace == "Y" and alt:
                return f"MIGRATION CANDIDATE: Evaluate migration to {alt} — improved licensing economics and long-term support."
            else:
                return f"SUPPORTED: No immediate action required. Extended support through {ext_end or 'N/A'}."
