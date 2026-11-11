# Start here

This folder is the complete ProductPulse AI project: SQL, Python, notebooks, a Streamlit report, a Power BI build kit, the Claude insight workflow and all documentation.

Four things can only be done by you, on your accounts and your computer. They are listed below in order. Everything else is already built.

## What is done and what is left

| Part | Status |
|---|---|
| Folder structure, `.gitignore`, `requirements.txt`, licence | Done |
| 34 BigQuery SQL queries in 7 files, 3 views, 12 export queries | Written. **Not yet run against BigQuery** (needs your Google account) |
| Python helper package, export script, 6 notebooks | Done and tested end to end on synthetic demo data |
| Streamlit report with "Ask about this report" | Written; logic tested, not yet opened in a browser |
| Power BI theme, DAX measures, page-by-page build guide | Done. **The `.pbix` must be assembled in Power BI Desktop** |
| Claude prompts, metric summary builder, validation log | Done |
| README, data dictionary, metric definitions, reports, interview prep | Done, with clearly marked blanks for your real numbers |
| Real numbers in the README and executive summary | **Blank on purpose** until step 2 below is run |

Why the blanks: the project's own rule is "never invent findings". Real numbers exist only after the queries run in your BigQuery project. The demo data in `data/demo/` is invented so you can test the code; it must not be quoted.

## Step 1. Set up Python (10 minutes)

Open **Command Prompt** in this folder (in File Explorer, click the address bar, type `cmd`, press Enter).

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Check that it works on the demo data:

```bat
python scripts\build_metric_summary.py
jupyter lab
```

Open `notebooks/01_data_exploration.ipynb` and choose Run > Run All Cells. You should see a "SYNTHETIC DEMO DATA" warning and charts.

## Step 2. Get the real data from BigQuery (20 minutes)

1. Go to <https://console.cloud.google.com/bigquery> and sign in with a Google account.
2. Create a project (top bar > project picker > New project). No credit card is needed for the BigQuery sandbox. Copy the **project ID** (not the name).
3. Optional but recommended: open `sql/01_schema_exploration.sql`, paste query Q01 into the BigQuery editor and run it. You should see 20201101 to 20210131.
4. Back in Command Prompt:

```bat
python scripts\export_from_bigquery.py --project YOUR_PROJECT_ID --dry-run
python scripts\export_from_bigquery.py --project YOUR_PROJECT_ID
```

The first run opens your browser to sign in. The script creates the `productpulse` dataset and views, runs the 12 export queries and saves CSV files in `data/exports/`. From this moment every notebook and the app use the real data automatically.

If a query fails with "Unrecognized name" or a type error, the live schema differs from what the SQL expects. Open the table schema in BigQuery, adjust the field in `sql/00_create_views.sql`, and run again. Note the change in `docs/project_log.md`.

## Step 3. Produce the real results (1 to 2 hours)

```bat
python scripts\build_metric_summary.py
jupyter lab
```

1. Run notebooks 01 to 06 in order (Run All Cells). Notebook 02 must end with no FAIL rows. Notebooks 03 and 04 must print "PASS" for the SQL reconciliation.
2. Under each chart, replace the *Interpretation* prompt with your own observation, explanation and next check.
3. Open `reports/kpi_snapshot.md`. These are your verified numbers.
4. Fill the blanks in `reports/executive_summary.md`, the *Key findings* section of `README.md`, and `data/data_dictionary.md`.
5. Optional: `streamlit run app\streamlit_app.py` to see the web report.

## Step 4. Build the Power BI report (2 to 3 hours)

Install Power BI Desktop from the Microsoft Store, then follow [`powerbi/BUILD_GUIDE.md`](powerbi/BUILD_GUIDE.md). It gives the model, every measure, every visual's fields and the SQL numbers each card must match. Save as `powerbi/ProductPulse.pbix` and export four screenshots to `powerbi/screenshots/`.

## Step 5. Claude insight workflow (30 minutes)

```bat
python scripts\ask_claude.py --print-prompt
```

Paste the output into claude.ai (or set `ANTHROPIC_API_KEY` to call the API). Then check every sentence using [`ai/insight_validation.md`](ai/insight_validation.md) and fill in its log table.

## Step 6. Publish to GitHub (15 minutes)

Create an empty repository called `ProductPulse-AI` on github.com first, then:

```bat
git init
git add .
git commit -m "Complete ProductPulse analytics portfolio"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ProductPulse-AI.git
git push -u origin main
```

Before pushing, run `git status` and confirm that `data/exports/`, `.venv/` and any `.env` file are **not** listed. Then go through [`docs/qa_checklist.md`](docs/qa_checklist.md).

## Step 7. Prepare to explain it

Read [`docs/interview_prep.md`](docs/interview_prep.md) and write your own numbers into the answers. Being able to open the query behind any number is the point of the project.

## Where everything is

| Folder | Contents |
|---|---|
| `sql/` | `00_create_views.sql`, seven analysis files (Q01 to Q34), `exports/` used by the script |
| `scripts/` | BigQuery export, metric summary builder, Claude helper, demo data generator |
| `productpulse/` | Shared Python functions: loading, KPIs, charts, insight prompt |
| `notebooks/` | Six notebooks, to be run in order |
| `app/` | Streamlit report |
| `powerbi/` | Theme, DAX measures, build guide, screenshots folder |
| `ai/` | Prompts, verified metrics, validation log |
| `reports/` | Executive summary, experiment memo, limitations, KPI snapshot |
| `docs/` | Architecture diagram, metric definitions, data flow, QA checklist, interview prep, project log |
| `data/` | Data dictionary, access notes, `demo/` (synthetic), `exports/` (your real export, git-ignored) |
