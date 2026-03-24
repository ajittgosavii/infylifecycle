"""
Agent 1: OS Data Fetcher
Verifies and updates OS lifecycle dates using Claude AI with web search.
"""
import anthropic
import json
import streamlit as st
from datetime import datetime


SEARCH_TARGETS = [
    ("Windows", "Windows 10 Windows 11 lifecycle support end dates 2025 2026 site:microsoft.com"),
    ("Windows Server", "Windows Server 2016 2019 2022 2025 lifecycle support end dates microsoft"),
    ("RHEL", "Red Hat Enterprise Linux RHEL 7 8 9 10 end of life support dates 2026"),
    ("Ubuntu", "Ubuntu LTS 20.04 22.04 24.04 end of life support dates 2026"),
    ("SQL Server", "SQL Server 2016 2017 2019 2022 lifecycle support end dates microsoft"),
]


class OSDataAgent:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-20250514"

    def fetch_updates(self, progress_callback=None) -> dict:
        """
        Uses Claude with web search to fetch latest OS lifecycle dates.
        Returns a dict of verified/updated date information keyed by OS name.
        """
        updates = {}
        total = len(SEARCH_TARGETS)

        for idx, (family, query) in enumerate(SEARCH_TARGETS):
            if progress_callback:
                progress_callback(idx / total, f"Searching: {family} lifecycle data...")

            try:
                result = self._search_lifecycle(family, query)
                updates[family] = result
            except Exception as e:
                updates[family] = {"error": str(e), "data": []}

        if progress_callback:
            progress_callback(1.0, "Web search complete.")

        return updates

    def _search_lifecycle(self, family: str, query: str) -> dict:
        """Call Claude with web_search to get lifecycle info for an OS family."""
        prompt = f"""Search for the latest support lifecycle end dates for {family} operating systems.
Query: {query}

After searching, return a JSON object with this structure (only JSON, no other text):
{{
  "family": "{family}",
  "fetched_at": "{datetime.now().isoformat()}",
  "versions": [
    {{
      "name": "exact version name e.g. Windows 11 24H2",
      "mainstream_end": "YYYY-MM-DD or descriptive string",
      "extended_end": "YYYY-MM-DD or empty string",
      "status": "Supported|End of Life|Expiring Soon|Future",
      "notes": "any important notes"
    }}
  ],
  "source_url": "the main URL where you found this information"
}}

Focus on accuracy. Only include versions you found confirmed data for."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract text content from response
        text_content = ""
        for block in response.content:
            if hasattr(block, "text"):
                text_content += block.text

        # Try to parse JSON from response
        try:
            clean = text_content.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            return json.loads(clean)
        except Exception:
            return {"family": family, "raw": text_content, "versions": [], "error": "parse_failed"}

    def merge_updates_into_df(self, df, updates: dict):
        """
        Merge fetched web data into the OS dataframe.
        Updates 'Notes' column with source info and flags any date discrepancies.
        """
        import pandas as pd
        df = df.copy()
        changes_log = []

        for family, result in updates.items():
            if "error" in result and result.get("versions") == []:
                continue
            versions = result.get("versions", [])
            for v in versions:
                name = v.get("name", "")
                mask = df["OS Version"].str.contains(
                    name.replace("(", r"\(").replace(")", r"\)"),
                    case=False, na=False, regex=True
                )
                if mask.any():
                    idx = df[mask].index[0]
                    old_mainstream = df.at[idx, "Mainstream/Full Support End"]
                    new_mainstream = v.get("mainstream_end", "")

                    # Flag discrepancy if date differs significantly
                    if new_mainstream and new_mainstream != old_mainstream:
                        note = df.at[idx, "Notes"] or ""
                        df.at[idx, "Notes"] = f"{note} [Web verified: {new_mainstream}]".strip()
                        changes_log.append(
                            f"⚠️ {name}: Mainstream end updated from '{old_mainstream}' → '{new_mainstream}'"
                        )

        return df, changes_log
