# Claude prompts

The insight assistant is allowed to see one thing: the verified aggregate metrics in `ai/verified_metrics.json`, built by `scripts/build_metric_summary.py`. It never receives raw events, user ids, credentials or anything it could use to "discover" a number on its own.

The prompts below are the single source of truth. The same text lives in code in `productpulse/insights.py`, which is what the Streamlit app and `scripts/ask_claude.py` send.

## How to run it

| Way | Command | Needs |
|---|---|---|
| Paste into claude.ai | `python scripts/ask_claude.py --print-prompt` then copy the output | Nothing |
| Script with the API | `python scripts/ask_claude.py --question "Summarize the report"` | `ANTHROPIC_API_KEY` environment variable, `pip install anthropic` |
| Streamlit panel | `streamlit run app/streamlit_app.py` > *Ask about this report* | Same as above for live answers |

Set the key in the terminal session only. Never write it in a file that Git tracks.

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."     # Windows PowerShell, current window only
```

The model name defaults to `claude-sonnet-5-5` and can be changed with the `CLAUDE_MODEL` environment variable. Check the current model list and pricing in the Anthropic API documentation before running.

## System prompt

```text
You are a careful product analytics assistant.

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
- Cohorts are based on first OBSERVED activity, and late cohorts are incomplete.
```

## User message template

```text
TASK: <one of the preset questions below>

Return exactly these sections:
## Observations
- 3 concise observations. End each with the metric ids used, e.g. [funnel_user_view_to_cart].
## Hypotheses (unproven)
- 2 hypotheses, each starting with "Hypothesis (unproven):".
## Recommended next analyses
- 3 follow-up analyses.
## Limitations
- The limitations that affect interpretation.

METRICS (verified aggregates, JSON):
<contents of ai/verified_metrics.json: id, name, value, numerator, denominator, unit, segment, definition, caveat>
```

## Preset questions

Free-text questions are deliberately not offered. Presets keep the assistant inside what the metrics can support.

| Button | Task text sent |
|---|---|
| Summarize the report | Give the standard summary of the supplied metrics. |
| Summarize the largest funnel drop-off | Focus on the funnel metrics. Which step loses the largest share of users or sessions, and how does the user-level funnel differ from the sequential session funnel? |
| Compare mobile and desktop conversion | Focus on the device metrics. Compare mobile and desktop at each funnel step. |
| Describe retention by cohort | Focus on the cohort retention metrics. Describe month-1 retention by cohort and state clearly which cohorts are incomplete. |
| Compare acquisition channels | Focus on the channel metrics. Compare user purchase conversion across channels and note which channel labels are obfuscation artefacts. |

## Why the prompt is built this way

| Design choice | What it prevents |
|---|---|
| Metrics arrive with numerator, denominator and segment | A rate quoted without its base, or against the wrong population |
| Every observation must end with metric ids | Statements that cannot be traced to a query |
| Hypotheses must start with "Hypothesis (unproven):" | A guess about cause being read as a finding |
| Caveats are in the system prompt | Causal language, and treating first-touch source as session source |
| Fixed output sections | Long narrative answers where unsupported claims hide |
| Aggregates only, preset questions only | Sending personal data, or asking about things the data cannot show |
| `find_unsupported_numbers()` runs on every answer | A number that is not in the input slipping through unnoticed |

None of this removes the human review. The validation steps are in [`insight_validation.md`](insight_validation.md).

## Prompts for using Claude as a reviewer

These are for your own learning and checking, not for the report.

```text
Here is a BigQuery SQL query and what I think it calculates. Tell me the grain of the
result, whether any join or UNNEST can multiply rows, and one validation query I should
run. Do not rewrite the query unless there is a bug.
```

```text
Here is a metric definition (name, numerator, denominator, grain, filters). List the
ways a product manager could misread it and what caveat I should add.
```

```text
I will paste a chart title, the axis labels and my one-paragraph interpretation.
Point out any sentence that claims a cause the data cannot support.
```
