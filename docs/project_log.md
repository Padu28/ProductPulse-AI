# Project log

A running record: question, method, result, limitation, next step. Add a row every working session. Interviewers often ask "what went wrong and what did you change?"; this is where the answer comes from.

| Date | Question | Method (file / query) | Result | Limitation | Next step |
|---|---|---|---|---|---|
| 2026-11-11 | Project scaffold | Repository structure, SQL, notebooks, app, Power BI kit and docs created; code tested on synthetic demo data | Pipeline runs end to end on demo data | SQL not yet run on BigQuery; no real numbers yet | Run `scripts/export_from_bigquery.py` |
| | What is the date range and size of the sample? | `01_schema_exploration.sql` Q01 | | | |
| | Which fields are null or obfuscated? | `02_data_quality.sql` Q07 | | | |
| | Is revenue double counted? | `02_data_quality.sql` Q11 | | | |
| | Where is the largest funnel drop-off? | `04_funnel_analysis.sql` Q19, Q21 | | | |
| | Does it differ by device? | Q20; notebook 03 | | | |
| | Do users return? | `05_cohort_retention.sql` Q23; notebook 04 | | | |

## Schema changes made

If a query failed and you changed a field name or type, record it here.

| Date | File | Change | Reason |
|---|---|---|---|
| | | | |
