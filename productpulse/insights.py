"""The grounded-insight workflow: verified metrics in, labelled draft out.

Claude only ever receives the aggregate metrics in ai/verified_metrics.json
plus their definitions and caveats. No raw events and no user ids.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI_DIR = ROOT / "ai"
DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")

SYSTEM_PROMPT = """You are a careful product analytics assistant.

Use only the metrics and definitions supplied below.
Do not invent values, causes, user quotes or business impact.
Separate:
1) observed facts,
2) plausible hypotheses to investigate,
3) recommended follow-up analyses.

For every observation, quote the metric id, metric name, value,
comparison period or segment, and denominator if supplied.
If the evidence is insufficient, say so.

Dataset caveats:
- Historical, obfuscated GA4 ecommerce sample (Google Merchandise Store).
- Observational data; it does not establish causality.
- The sample covers 2020-11-01 through 2021-01-31.
- Traffic source is user-level first-touch attribution.
- Cohorts are based on first OBSERVED activity, and late cohorts are incomplete."""

OUTPUT_FORMAT = """Return exactly these sections:
## Observations
- 3 concise observations. End each with the metric ids used, e.g. [funnel_user_view_to_cart].
## Hypotheses (unproven)
- 2 hypotheses, each starting with "Hypothesis (unproven):".
## Recommended next analyses
- 3 follow-up analyses.
## Limitations
- The limitations that affect interpretation."""

PRESET_QUESTIONS = {
    "Summarize the report": "Give the standard summary of the supplied metrics.",
    "Summarize the largest funnel drop-off":
        "Focus on the funnel metrics. Which step loses the largest share of users or sessions, "
        "and how does the user-level funnel differ from the sequential session funnel?",
    "Compare mobile and desktop conversion":
        "Focus on the device metrics. Compare mobile and desktop at each funnel step.",
    "Describe retention by cohort":
        "Focus on the cohort retention metrics. Describe month-1 retention by cohort and "
        "state clearly which cohorts are incomplete.",
    "Compare acquisition channels":
        "Focus on the channel metrics. Compare user purchase conversion across channels and "
        "note which channel labels are obfuscation artefacts.",
}


def metrics_path(prefer_real: bool = True) -> Path:
    real, demo = AI_DIR / "verified_metrics.json", AI_DIR / "verified_metrics.DEMO.json"
    if prefer_real and real.exists():
        return real
    if demo.exists():
        return demo
    raise FileNotFoundError("Run `python scripts/build_metric_summary.py` first.")


def load_metrics(path: Path | None = None) -> dict:
    return json.loads((path or metrics_path()).read_text(encoding="utf-8"))


def select_metrics(summary: dict, groups: list[str] | None = None) -> dict:
    """Keep only some metric groups (e.g. ['funnel', 'device']) to keep the prompt focused."""
    if not groups:
        return summary
    kept = [m for m in summary["metrics"] if m["group"] in groups]
    return {**summary, "metrics": kept}


def build_prompt(summary: dict, question: str = "Give the standard summary of the supplied metrics.") -> str:
    """The exact user message sent to Claude (also what you paste into claude.ai)."""
    compact = {
        "data_source": summary["data_source"],
        "reporting_period": summary["reporting_period"],
        "metrics": [{k: m[k] for k in ("id", "name", "value_formatted", "numerator", "denominator",
                                       "unit", "segment", "definition", "caveat") if m.get(k) is not None}
                    for m in summary["metrics"]],
    }
    return (f"TASK: {question}\n\n{OUTPUT_FORMAT}\n\n"
            f"METRICS (verified aggregates, JSON):\n{json.dumps(compact, indent=1)}")


def ask_claude(summary: dict, question: str, model: str | None = None, max_tokens: int = 1200) -> str:
    """Send the grounded prompt to the Anthropic API. Needs ANTHROPIC_API_KEY in the environment."""
    import anthropic  # imported here so the rest of the project works without it

    client = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY from the environment
    response = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(summary, question)}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def find_unsupported_numbers(answer: str, summary: dict) -> list[str]:
    """First-pass check: list numbers in the answer that do not appear in the supplied metrics.

    This is a helper for the human reviewer, not a replacement. A number can be
    "found" and still be used in a misleading sentence.
    """
    import re

    allowed = set()
    for m in summary["metrics"]:
        for field in ("value_formatted", "numerator", "denominator", "segment", "name"):
            for tok in re.findall(r"\d[\d,]*\.?\d*", str(m.get(field, ""))):
                allowed.add(tok.replace(",", "").rstrip("."))
    for tok in re.findall(r"\d[\d,]*\.?\d*", json.dumps(summary["reporting_period"])):
        allowed.add(tok.replace(",", "").rstrip("."))
    flagged = []
    for tok in re.findall(r"\d[\d,]*\.?\d*", answer):
        clean = tok.replace(",", "").rstrip(".")
        if clean in allowed or clean in {"1", "2", "3", "0", "30", "7"}:
            continue
        if clean not in flagged:
            flagged.append(clean)
    return flagged
