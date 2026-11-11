"""Draft an insight summary with Claude from the verified metrics only.

With an API key (recommended way to keep it out of the code):
    Windows PowerShell:  $env:ANTHROPIC_API_KEY = "sk-ant-..."
    then:                python scripts/ask_claude.py

Without an API key the script prints the exact prompt, which you can paste
into claude.ai. Either way the draft must be checked line by line using
ai/insight_validation.md before anything is reported.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from productpulse import insights  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--question", default="Summarize the report", choices=list(insights.PRESET_QUESTIONS))
    parser.add_argument("--print-prompt", action="store_true", help="Only print the prompt")
    args = parser.parse_args()

    summary = insights.load_metrics()
    question = insights.PRESET_QUESTIONS[args.question]
    prompt = insights.build_prompt(summary, question)

    if args.print_prompt or not os.environ.get("ANTHROPIC_API_KEY"):
        print("=== SYSTEM PROMPT ===\n" + insights.SYSTEM_PROMPT)
        print("\n=== USER MESSAGE ===\n" + prompt)
        if not args.print_prompt:
            print("\n(No ANTHROPIC_API_KEY set: paste the two parts above into claude.ai.)")
        return

    answer = insights.ask_claude(summary, question)
    flagged = insights.find_unsupported_numbers(answer, summary)
    out_dir = ROOT / "ai" / "outputs"
    out_dir.mkdir(exist_ok=True)
    tag = "DEMO_" if summary.get("is_demo") else ""
    path = out_dir / f"{tag}insight_draft_{date.today().isoformat()}.md"
    header = (f"<!-- UNREVIEWED AI DRAFT. Source: {summary['data_source']}. "
              f"Period: {summary['reporting_period']['start']} to {summary['reporting_period']['end']}. -->\n\n")
    path.write_text(header + answer + "\n", encoding="utf-8")
    print(answer)
    print(f"\nSaved to {path.relative_to(ROOT)}")
    print("Numbers not found in the supplied metrics (check each one):", flagged or "none")


if __name__ == "__main__":
    main()
