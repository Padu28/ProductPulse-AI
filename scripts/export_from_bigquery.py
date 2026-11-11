"""Export the ProductPulse tables from BigQuery to data/exports/*.csv.

What it does
------------
1. Signs in to Google (opens your browser the first time).
2. Creates the `productpulse` dataset in your project if it is missing.
3. Creates the three views in sql/00_create_views.sql.
4. Runs every query in sql/exports/ and saves each result as a CSV with the
   same name in data/exports/.
5. Copies the small AGGREGATE tables (no user ids) to data/samples/ so they
   can be committed to GitHub.

Usage
-----
    python scripts/export_from_bigquery.py --project YOUR_PROJECT_ID
    python scripts/export_from_bigquery.py --project YOUR_PROJECT_ID --dry-run

The BigQuery sandbox (no credit card) is enough: the whole public sample is
small compared with the 1 TB of free querying per month. Use --dry-run first
to see how many bytes each query would scan.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
EXPORT_SQL_DIR = SQL_DIR / "exports"
OUT_DIR = ROOT / "data" / "exports"
SAMPLES_DIR = ROOT / "data" / "samples"

# Aggregates that contain no user-level rows: safe to commit as small samples.
SHAREABLE = ["dataset_overview", "event_overview", "event_param_keys", "daily_metrics",
             "user_funnel_by_device", "session_funnel", "cohort_retention_monthly",
             "product_performance", "data_quality"]


def get_client(project: str):
    from google.cloud import bigquery
    import google.auth
    from google.auth.exceptions import DefaultCredentialsError

    scopes = ["https://www.googleapis.com/auth/bigquery"]
    try:
        credentials, _ = google.auth.default(scopes=scopes)
    except DefaultCredentialsError:
        # No gcloud login found: fall back to a browser sign-in.
        import pydata_google_auth
        credentials = pydata_google_auth.get_user_credentials(scopes)
    return bigquery.Client(project=project, credentials=credentials)


def prepare(sql: str, project: str, dataset: str) -> str:
    return sql.replace("YOUR_PROJECT.productpulse.", f"{project}.{dataset}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="Your Google Cloud project ID")
    parser.add_argument("--dataset", default="productpulse", help="Dataset for the views (default: productpulse)")
    parser.add_argument("--only", nargs="*", help="Export only these tables, e.g. --only daily_metrics dim_user")
    parser.add_argument("--skip-views", action="store_true", help="Do not (re)create the views")
    parser.add_argument("--dry-run", action="store_true", help="Only estimate bytes scanned; write nothing")
    args = parser.parse_args()

    from google.cloud import bigquery

    client = get_client(args.project)
    print(f"Connected to project: {args.project}")

    if not args.skip_views:      # views cost nothing to create and the dry run needs them
        dataset_ref = bigquery.Dataset(f"{args.project}.{args.dataset}")
        dataset_ref.location = "US"          # the public GA4 sample is stored in US
        client.create_dataset(dataset_ref, exists_ok=True)
        views_sql = prepare((SQL_DIR / "00_create_views.sql").read_text(encoding="utf-8"),
                            args.project, args.dataset)
        client.query(views_sql).result()
        print(f"Views created in {args.project}.{args.dataset}: events_base, items_base, sessions_base")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(EXPORT_SQL_DIR.glob("*.sql"))
    if args.only:
        files = [f for f in files if f.stem in set(args.only)]
    if not files:
        print("No export queries matched.")
        return 1

    total_bytes = 0
    for path in files:
        sql = prepare(path.read_text(encoding="utf-8"), args.project, args.dataset)
        if args.dry_run:
            job = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
            total_bytes += job.total_bytes_processed
            print(f"  {path.stem:<28} would scan {job.total_bytes_processed / 1e9:6.2f} GB")
            continue
        job = client.query(sql)
        df = job.to_dataframe()
        total_bytes += job.total_bytes_processed or 0
        df.to_csv(OUT_DIR / f"{path.stem}.csv", index=False)
        print(f"  {path.stem:<28} {len(df):>9,} rows   ({(job.total_bytes_processed or 0) / 1e9:.2f} GB scanned)")
        if path.stem in SHAREABLE:
            shutil.copyfile(OUT_DIR / f"{path.stem}.csv", SAMPLES_DIR / f"{path.stem}.csv")

    print(f"\nTotal scanned: {total_bytes / 1e9:.2f} GB")
    if not args.dry_run:
        print(f"CSV files are in: {OUT_DIR}")
        print("Next: python scripts/build_metric_summary.py   then open the notebooks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
