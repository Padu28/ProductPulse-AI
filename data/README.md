# Data

No raw data is stored in this repository. The analysis is reproduced from a public BigQuery dataset with the SQL in `sql/`.

## Source

| | |
|---|---|
| Dataset | `bigquery-public-data.ga4_obfuscated_sample_ecommerce` |
| Tables | `events_20201101` to `events_20210131` (query them together as `events_*` with `_TABLE_SUFFIX`) |
| Content | Obfuscated Google Analytics 4 events from the Google Merchandise Store |
| Location | US multi-region |
| Documentation | Google's "BigQuery sample dataset for Google Analytics ecommerce web implementation" page |

## How to access it

1. Sign in at <https://console.cloud.google.com/bigquery>.
2. Create or select a project. The BigQuery sandbox needs no billing account and includes 1 TB of free querying per month, far more than this dataset needs.
3. In Explorer, choose Add > Star a project by name > `bigquery-public-data`, then open `ga4_obfuscated_sample_ecommerce`.
4. Open any `events_` table and read the Schema tab before writing queries.
5. Run `sql/01_schema_exploration.sql` Q01 and check the cost estimate shown before you click Run.

## How the project gets its tables

```bat
python scripts\export_from_bigquery.py --project YOUR_PROJECT_ID
```

| Folder | Content | In Git? |
|---|---|---|
| `data/exports/` | Real export: 12 CSV files. `fact_user_day.csv` and `dim_user.csv` contain the obfuscated `user_pseudo_id` | No (git-ignored) |
| `data/samples/` | Copies of the small aggregate tables only (no user-level rows) | Yes |
| `data/demo/` | **Synthetic** tables from `scripts/make_demo_data.py`, same columns, invented values | Yes |
| `data/simulated/` | **Simulated** A/B test data from notebook 05 | Yes |

The loaders in `productpulse/data.py` use `data/exports/` when it exists and fall back to `data/demo/` otherwise. Every notebook prints which one is loaded.

## Exported tables

| File | Grain | Used by |
|---|---|---|
| `dataset_overview.csv` | One row | Notebook 01, 02 |
| `event_overview.csv` | Event name | Notebook 01 |
| `event_param_keys.csv` | Parameter key | Data dictionary |
| `daily_metrics.csv` | Day | Notebook 01, 02 |
| `dim_user.csv` | User | Notebooks, Power BI, app |
| `fact_user_day.csv` | User x day | Notebooks, Power BI, app |
| `user_funnel_by_device.csv` | Device | Reconciliation in notebook 03 |
| `session_funnel.csv` | Device x channel | Sequential funnel |
| `cohort_retention_monthly.csv` | Cohort month x month number | Reconciliation in notebook 04 |
| `product_performance.csv` | Product | Product page |
| `transactions.csv` | Validated order | Notebook 02 |
| `data_quality.csv` | Check | Notebook 02 |

Column-level documentation: [`data_dictionary.md`](data_dictionary.md).

## Rules

- Never commit credentials, service-account JSON files or API keys.
- Do not upload a full copy of the dataset. Share the SQL and the access steps instead.
- Never present `data/demo/` or `data/simulated/` numbers as findings.
