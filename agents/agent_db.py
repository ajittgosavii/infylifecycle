"""
Agent 2: AI Recommendation Engine
Generates expert migration recommendations for every OS and DB row.
Uses OpenAI gpt-4o-mini (cheap, fast, no tools needed).
"""

from openai import OpenAI
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

WS_SYSTEM = f"""You are a senior web infrastructure architect with 25+ years of experience.
Today is {CURRENT_DATE}.

For each web server entry, generate a concise, actionable 1-2 sentence recommendation based on:
- Status (End of Life / Expiring Soon / Supported)
- Support end dates relative to today
- Version currency and security implications
- Upgrade path and alternatives listed

Classification guide:
- End of Life → CRITICAL: Upgrade immediately, cite unpatched CVE risk
- Expiring Soon → URGENT: Begin upgrade project now
- Old but supported → PLAN AHEAD: Schedule upgrade during next maintenance window
- Current stable → SUPPORTED: Monitor for new releases
Be specific: name exact target versions."""

AS_SYSTEM = f"""You are a senior middleware and application server architect with 25+ years of experience.
Today is {CURRENT_DATE}.

For each application server / middleware entry, generate a concise, actionable 1-2 sentence recommendation based on:
- Status (End of Life / Expiring Soon / Supported)
- Support end dates and vendor lifecycle policies
- Jakarta EE / Java EE version compatibility implications
- Container/cloud-native migration opportunities

Classification guide:
- End of Life → CRITICAL: No patches available, migrate immediately
- Expiring Soon → URGENT: Plan migration before support ends
- Supported with newer available → PLAN AHEAD: Evaluate upgrade path
- Current → SUPPORTED: Monitor vendor announcements
Be specific: name exact target versions and migration paths."""

FW_SYSTEM = f"""You are a senior software development platform architect with 25+ years of experience.
Today is {CURRENT_DATE}.

For each framework / runtime entry, generate a concise, actionable 1-2 sentence recommendation based on:
- Status (End of Life / Expiring Soon / Supported / Future)
- Support end dates and LTS policies
- Breaking changes and migration complexity
- Security patch availability

Classification guide:
- End of Life → CRITICAL: No security patches, upgrade immediately
- Expiring Soon → URGENT: Begin migration to current LTS
- Current non-LTS → PLAN AHEAD: Move to LTS before STS support ends
- Current LTS → SUPPORTED: Monitor next LTS release
- Future → MONITOR: Track for greenfield projects
Be specific: name exact target versions and note breaking changes."""

BATCH_PROMPT_GENERIC = """Generate recommendations for these {kind_label} entries. Return ONLY a valid JSON object mapping the entry key to its recommendation text (no markdown fences, no preamble):

{rows}

Expected format:
{{"Entry Key": "recommendation text", ...}}"""


class RecommendationAgent:
    def __init__(self, api_key: str):
        self.client     = OpenAI(api_key=api_key)
        self.model      = "gpt-4o-mini"   # cheap, fast, no tools needed
        self.batch_size = 20

    # ── OS recommendations ────────────────────────────────────────────────────
    def generate_os_recommendations(self, df: pd.DataFrame,
                                     progress_callback=None) -> pd.DataFrame:
        df = df.copy()
        rows      = df.to_dict("records")
        recs      = {}
        total     = len(rows)
        ai_count  = 0
        rb_count  = 0

        for i in range(0, total, self.batch_size):
            batch = rows[i:i + self.batch_size]
            if progress_callback:
                progress_callback(
                    i / total,
                    f"🤖 OpenAI (gpt-4o-mini) — OS: rows {i+1}–{min(i+self.batch_size, total)} of {total}"
                )
            batch_recs, used_ai = self._recommend_batch(batch, kind="OS")
            recs.update(batch_recs)
            if used_ai:
                ai_count += len(batch)
            else:
                rb_count += len(batch)
                if progress_callback:
                    progress_callback(i / total,
                        f"⚠️ OS batch {i+1}–{min(i+self.batch_size,total)}: "
                        f"OpenAI failed — rule-based fallback used")

        for idx, row in df.iterrows():
            key = row["OS Version"]
            if key in recs:
                df.at[idx, "Recommendation"] = recs[key]

        if progress_callback:
            if rb_count == total:
                progress_callback(1.0,
                    f"❌ OS recs: OpenAI failed all batches — {rb_count} rows used rule-based. "
                    f"Check API key quota.")
            elif rb_count > 0:
                progress_callback(1.0,
                    f"⚠️ OS recs: OpenAI {ai_count} rows ✅ | Rule-based {rb_count} rows ⚠️")
            else:
                progress_callback(1.0,
                    f"✅ OS recs complete — OpenAI analysed all {ai_count} rows")
        return df

    # ── DB recommendations ────────────────────────────────────────────────────
    def generate_db_recommendations(self, df: pd.DataFrame,
                                     progress_callback=None) -> pd.DataFrame:
        df = df.copy()
        rows      = df.to_dict("records")
        recs      = {}
        total     = len(rows)
        ai_count  = 0
        rb_count  = 0

        for i in range(0, total, self.batch_size):
            batch = rows[i:i + self.batch_size]
            if progress_callback:
                progress_callback(
                    i / total,
                    f"🤖 OpenAI (gpt-4o-mini) — DB: rows {i+1}–{min(i+self.batch_size, total)} of {total}"
                )
            batch_recs, used_ai = self._recommend_batch(batch, kind="DB")
            recs.update(batch_recs)
            if used_ai:
                ai_count += len(batch)
            else:
                rb_count += len(batch)
                if progress_callback:
                    progress_callback(i / total,
                        f"⚠️ DB batch {i+1}–{min(i+self.batch_size,total)}: "
                        f"OpenAI failed — rule-based fallback used")

        for idx, row in df.iterrows():
            key = f"{row['Database']} {row['Version']}"
            if key in recs:
                df.at[idx, "Recommendation"] = recs[key]

        if progress_callback:
            if rb_count == total:
                progress_callback(1.0,
                    f"❌ DB recs: OpenAI failed all batches — {rb_count} rows used rule-based. "
                    f"Check API key quota.")
            elif rb_count > 0:
                progress_callback(1.0,
                    f"⚠️ DB recs: OpenAI {ai_count} rows ✅ | Rule-based {rb_count} rows ⚠️")
            else:
                progress_callback(1.0,
                    f"✅ DB recs complete — OpenAI analysed all {ai_count} rows")
        return df

    # ── Generic recommendations for WS / AS / FW ──────────────────────────────
    def generate_generic_recommendations(self, df: pd.DataFrame, kind: str,
                                          name_col: str,
                                          progress_callback=None) -> pd.DataFrame:
        """Generate recommendations for WS, AS, or FW dataframes."""
        df = df.copy()
        rows      = df.to_dict("records")
        recs      = {}
        total     = len(rows)
        ai_count  = 0
        rb_count  = 0
        label     = {"WS": "Web Server", "AS": "App Server", "FW": "Framework"}.get(kind, kind)

        for i in range(0, total, self.batch_size):
            batch = rows[i:i + self.batch_size]
            if progress_callback:
                progress_callback(
                    i / total,
                    f"🤖 OpenAI (gpt-4o-mini) — {label}: rows {i+1}–{min(i+self.batch_size, total)} of {total}"
                )
            batch_recs, used_ai = self._recommend_batch(batch, kind=kind)
            recs.update(batch_recs)
            if used_ai:
                ai_count += len(batch)
            else:
                rb_count += len(batch)
                if progress_callback:
                    progress_callback(i / total,
                        f"⚠️ {label} batch {i+1}–{min(i+self.batch_size,total)}: "
                        f"OpenAI failed — rule-based fallback used")

        for idx, row in df.iterrows():
            key = f"{row[name_col]} {row.get('Version', '')}".strip()
            if key in recs:
                df.at[idx, "Recommendation"] = recs[key]

        if progress_callback:
            if rb_count == total:
                progress_callback(1.0,
                    f"❌ {label} recs: OpenAI failed all batches — {rb_count} rows used rule-based.")
            elif rb_count > 0:
                progress_callback(1.0,
                    f"⚠️ {label} recs: OpenAI {ai_count} rows ✅ | Rule-based {rb_count} rows ⚠️")
            else:
                progress_callback(1.0,
                    f"✅ {label} recs complete — OpenAI analysed all {ai_count} rows")
        return df

    # ── Internal batch call ───────────────────────────────────────────────────
    def _recommend_batch(self, batch: list, kind: str) -> tuple:
        """Returns (recs_dict, used_ai: bool)."""
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
            prompt = BATCH_PROMPT_OS.format(rows=rows_text)
            system = OS_SYSTEM
            key_fn = lambda r: r.get("OS Version", "")
        elif kind == "DB":
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
            prompt = BATCH_PROMPT_DB.format(rows=rows_text)
            system = DB_SYSTEM
            key_fn = lambda r: f"{r.get('Database','?')} {r.get('Version','?')}"
        elif kind == "WS":
            name_col = "Web Server"
            rows_text = "\n".join(
                f"- {r.get(name_col,'?')} {r.get('Version','?')} | Type: {r.get('Type','')} "
                f"| Status: {r.get('Status','')} "
                f"| Mainstream End: {r.get('Mainstream / Premier End','')} "
                f"| Extended End: {r.get('Extended Support End','')} "
                f"| Upgrade: {r.get('Upgrade','')} | Replace: {r.get('Replace','')} "
                f"| Primary Alt: {r.get('Primary Alternative','')} "
                f"| Notes: {r.get('Notes','')}"
                for r in batch
            )
            prompt = BATCH_PROMPT_GENERIC.format(kind_label="web server", rows=rows_text)
            system = WS_SYSTEM
            key_fn = lambda r: f"{r.get(name_col,'?')} {r.get('Version','?')}"
        elif kind == "AS":
            name_col = "App Server"
            rows_text = "\n".join(
                f"- {r.get(name_col,'?')} {r.get('Version','?')} | Type: {r.get('Type','')} "
                f"| Status: {r.get('Status','')} "
                f"| Mainstream End: {r.get('Mainstream / Premier End','')} "
                f"| Extended End: {r.get('Extended Support End','')} "
                f"| Upgrade: {r.get('Upgrade','')} | Replace: {r.get('Replace','')} "
                f"| Primary Alt: {r.get('Primary Alternative','')} "
                f"| Notes: {r.get('Notes','')}"
                for r in batch
            )
            prompt = BATCH_PROMPT_GENERIC.format(kind_label="application server / middleware", rows=rows_text)
            system = AS_SYSTEM
            key_fn = lambda r: f"{r.get(name_col,'?')} {r.get('Version','?')}"
        else:  # FW
            name_col = "Framework"
            rows_text = "\n".join(
                f"- {r.get(name_col,'?')} {r.get('Version','?')} | Type: {r.get('Type','')} "
                f"| Status: {r.get('Status','')} "
                f"| Mainstream End: {r.get('Mainstream / Premier End','')} "
                f"| Extended End: {r.get('Extended Support End','')} "
                f"| Upgrade: {r.get('Upgrade','')} | Replace: {r.get('Replace','')} "
                f"| Primary Alt: {r.get('Primary Alternative','')} "
                f"| Notes: {r.get('Notes','')}"
                for r in batch
            )
            prompt = BATCH_PROMPT_GENERIC.format(kind_label="framework / runtime", rows=rows_text)
            system = FW_SYSTEM
            key_fn = lambda r: f"{r.get(name_col,'?')} {r.get('Version','?')}"

        # Attempt: OpenAI Chat Completions API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt}
                ]
            )
            text = response.choices[0].message.content.strip()
            for fence in ("```json", "```"):
                if fence in text:
                    text = text.split(fence, 1)[-1].split("```", 1)[0].strip()
                    break
            result = json.loads(text)
            if result:
                return result, True   # ✅ OpenAI succeeded

        except Exception as e:
            self._last_error = str(e)

        # Fallback: rule-based (AI failed)
        return {key_fn(r): self._rule_based(r, kind) for r in batch}, False

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
            # Handles DB, WS, AS, FW — all share same column structure
            status  = row.get("Status", "").lower()
            alt     = row.get("Primary Alternative", "")
            ext_end = row.get("Extended Support End", "") or row.get("Mainstream / Premier End", "")
            replace = row.get("Replace", "N")
            # Determine name based on kind
            name_col_map = {"DB": "Database", "WS": "Web Server", "AS": "App Server", "FW": "Framework"}
            name_col = name_col_map.get(kind, "Database")
            item_name = f"{row.get(name_col, kind)} {row.get('Version', '')}".strip()

            if status == "end of life":
                return f"CRITICAL: {item_name} is End of Life. Migrate{' to ' + alt if alt else ''} immediately — no patches or security fixes available."
            elif status == "expiring soon":
                return f"URGENT: Support ending soon (end: {ext_end}). Begin migration{' to ' + alt if alt else ''} immediately."
            elif status == "future":
                return f"MONITOR: {item_name} is not yet released. Track GA timeline for new project adoption."
            elif replace == "Y" and alt:
                return f"MIGRATION CANDIDATE: Evaluate migration to {alt} for long-term support."
            else:
                return f"SUPPORTED: No immediate action required. Support through {ext_end or 'N/A'}."
