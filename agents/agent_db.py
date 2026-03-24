"""
Agent 2: Recommendation Engine
Expert AI agent that generates actionable migration recommendations for OS and DB versions.
Uses Claude AI to analyse support status, lifecycle dates, and migration paths.
"""
import anthropic
import json
import pandas as pd
from datetime import datetime


CURRENT_DATE = "March 2026"

OS_SYSTEM_PROMPT = f"""You are a senior enterprise IT architect at Infosys with deep expertise in OS lifecycle management, 
Microsoft Windows, RHEL, Ubuntu, Solaris, AIX, HP-UX, and other enterprise operating systems.
Today's date is {CURRENT_DATE}.

Your task: Generate concise, actionable recommendations for each OS version entry based on its support lifecycle.

Recommendation rules:
- End of Life (all support dates past): "CRITICAL: Immediately migrate to [best alternative]. Security risk - no patches available."
- Expiring within 6 months: "URGENT: Plan migration before [date]. Upgrade to [version] recommended."
- Expiring within 12 months: "HIGH PRIORITY: Schedule upgrade to [version] within 6 months."
- Expiring within 24 months: "PLAN AHEAD: Initiate upgrade planning to [version]. Target completion: [date]."
- Supported >24 months: "SUPPORTED: No immediate action required. Monitor for [next version]."
- Replace=Y flagged: "REPLACE RECOMMENDED: Migrate to [Primary Alternative] for long-term supportability."
- Future/not yet released: "MONITOR: Track release timeline. Plan architecture for adoption."

Keep each recommendation to 1-2 sentences. Be specific with version names and dates."""

DB_SYSTEM_PROMPT = f"""You are a senior database architect and migration expert at Infosys with deep expertise in 
SQL Server, Oracle, PostgreSQL, MySQL, MariaDB, MongoDB, Redis, IBM Db2 and other enterprise databases.
Today's date is {CURRENT_DATE}.

Your task: Generate concise, actionable recommendations for each database version entry.

Recommendation rules:
- End of Life: "CRITICAL: Migrate to [specific recommended version] immediately. [Risk description]."
- Expiring Soon (within 12 months): "URGENT: Begin migration to [version] — extended support ends [date]."
- Supported with Replace=Y: "MIGRATION CANDIDATE: Evaluate migration to [Primary Alternative] for cost/licensing benefits."
- Supported, no flag: "SUPPORTED: No action needed until [end date]. Plan for [next LTS] adoption."
- Future release: "WATCH: Evaluate [version] upon GA release for new project deployments."
- Oracle versions: Always note licensing cost reduction opportunity with PostgreSQL alternative.

Keep each recommendation to 1-2 sentences. Include specific version targets and dates."""


class RecommendationAgent:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-20250514"

    def generate_os_recommendations(self, df: pd.DataFrame, progress_callback=None) -> pd.DataFrame:
        """Generate AI recommendations for the OS Versions sheet."""
        df = df.copy()
        batch_size = 20
        rows = df.to_dict("records")
        all_recs = {}

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            if progress_callback:
                pct = i / len(rows)
                progress_callback(pct, f"Analysing OS rows {i+1}–{min(i+batch_size, len(rows))} of {len(rows)}...")

            recs = self._call_recommendation_api(batch, "OS", OS_SYSTEM_PROMPT)
            all_recs.update(recs)

        for idx, row in df.iterrows():
            key = row["OS Version"]
            if key in all_recs:
                df.at[idx, "Recommendation"] = all_recs[key]

        if progress_callback:
            progress_callback(1.0, "OS recommendations complete.")

        return df

    def generate_db_recommendations(self, df: pd.DataFrame, progress_callback=None) -> pd.DataFrame:
        """Generate AI recommendations for the DB Versions sheet."""
        df = df.copy()
        batch_size = 15
        rows = df.to_dict("records")
        all_recs = {}

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            if progress_callback:
                pct = i / len(rows)
                progress_callback(pct, f"Analysing DB rows {i+1}–{min(i+batch_size, len(rows))} of {len(rows)}...")

            recs = self._call_recommendation_api(batch, "DB", DB_SYSTEM_PROMPT)
            all_recs.update(recs)

        for idx, row in df.iterrows():
            key = f"{row['Database']} {row['Version']}"
            if key in all_recs:
                df.at[idx, "Recommendation"] = all_recs[key]

        if progress_callback:
            progress_callback(1.0, "DB recommendations complete.")

        return df

    def _call_recommendation_api(self, batch: list, sheet_type: str, system_prompt: str) -> dict:
        """Call Claude API to generate recommendations for a batch of rows."""
        if sheet_type == "OS":
            rows_text = "\n".join([
                f"- {r['OS Version']} | Available: {r['Availability Date']} | "
                f"Mainstream End: {r['Mainstream/Full Support End']} | "
                f"Extended End: {r['Extended/LTSC Support End']} | "
                f"Upgrade: {r['Upgrade']} | Replace: {r['Replace']} | "
                f"Alt: {r['Primary Alternative']} | Notes: {r['Notes']}"
                for r in batch
            ])
            key_field = "OS Version"
        else:
            rows_text = "\n".join([
                f"- {r['Database']} {r['Version']} | Type: {r['Type']} | "
                f"Status: {r['Status']} | Mainstream End: {r['Mainstream / Premier End']} | "
                f"Extended End: {r['Extended Support End']} | "
                f"Upgrade: {r['Upgrade']} | Replace: {r['Replace']} | "
                f"Primary Alt: {r['Primary Alternative']} | Notes: {r['Notes']}"
                for r in batch
            ])
            key_field = "DB_KEY"

        prompt = f"""Generate recommendations for the following {sheet_type} versions:

{rows_text}

Return ONLY a valid JSON object (no markdown, no preamble) mapping each identifier to its recommendation:
{{
  "{batch[0][key_field] if sheet_type == 'OS' else f"{batch[0]['Database']} {batch[0]['Version']}"}": "recommendation text here",
  ...
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text.strip()
            # Strip markdown code fences if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            return json.loads(text)

        except Exception as e:
            # Fallback: return rule-based recommendations
            return self._fallback_recommendations(batch, sheet_type)

    def _fallback_recommendations(self, batch: list, sheet_type: str) -> dict:
        """Rule-based fallback recommendations when API fails."""
        result = {}
        today = datetime(2026, 3, 23)

        if sheet_type == "OS":
            for r in batch:
                key = r["OS Version"]
                mainstream = r.get("Mainstream/Full Support End", "")
                replace = r.get("Replace", "")
                upgrade = r.get("Upgrade", "")
                alt = r.get("Primary Alternative", "")

                if replace == "Y" and alt:
                    result[key] = f"MIGRATION RECOMMENDED: Plan migration to {alt} for enterprise supportability."
                elif upgrade == "Y":
                    result[key] = "UPGRADE REQUIRED: This version requires upgrade. Review support dates and plan transition."
                elif mainstream and mainstream not in ("", "Active", "Extended"):
                    try:
                        end_dt = datetime.strptime(mainstream[:10], "%Y-%m-%d")
                        days = (end_dt - today).days
                        if days < 0:
                            result[key] = "CRITICAL: Support has ended. Upgrade immediately to a supported version."
                        elif days < 180:
                            result[key] = f"URGENT: Support ends {mainstream}. Upgrade within 3 months."
                        elif days < 365:
                            result[key] = f"HIGH PRIORITY: Support ends {mainstream}. Begin upgrade planning now."
                        else:
                            result[key] = f"SUPPORTED: Monitor lifecycle. Support ends {mainstream}."
                    except Exception:
                        result[key] = "Review support dates and plan upgrade path accordingly."
                else:
                    result[key] = "Review support lifecycle and plan upgrade path accordingly."
        else:
            for r in batch:
                key = f"{r['Database']} {r['Version']}"
                status = r.get("Status", "")
                alt = r.get("Primary Alternative", "")
                ext_end = r.get("Extended Support End", "")

                if status == "End of Life":
                    result[key] = f"CRITICAL: End of Life. Migrate immediately{f' to {alt}' if alt else ''}."
                elif status == "Expiring Soon":
                    result[key] = f"URGENT: Support expiring soon. Plan migration{f' to {alt}' if alt else ''} immediately."
                elif status == "Future":
                    result[key] = "MONITOR: Future release. Evaluate upon GA for new deployments."
                elif r.get("Replace") == "Y" and alt:
                    result[key] = f"MIGRATION CANDIDATE: Evaluate migration to {alt} for licensing and support benefits."
                else:
                    result[key] = f"SUPPORTED: No immediate action needed. Extended support ends {ext_end or 'N/A'}."

        return result
