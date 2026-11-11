"""Loading the exported aggregate tables.

The project reads CSV files that were exported from BigQuery by
`scripts/export_from_bigquery.py` into `data/exports/`.

If that folder is empty, the loaders fall back to `data/demo/`, which holds
SYNTHETIC data made by `scripts/make_demo_data.py`. Demo data exists only so
you can check that the code runs. Numbers from it are NOT findings.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "data" / "exports"
DEMO_DIR = ROOT / "data" / "demo"

# Columns that hold dates, per table.
DATE_COLUMNS = {
    "dataset_overview": ["first_event_date", "last_event_date"],
    "daily_metrics": ["event_dt"],
    "dim_user": ["first_seen_dt", "last_seen_dt", "cohort_month"],
    "fact_user_day": ["event_dt"],
    "cohort_retention_monthly": ["cohort_month"],
    "transactions": ["purchase_dt"],
}

REQUIRED_TABLES = ["fact_user_day", "dim_user"]


def get_data_dir() -> tuple[Path, bool]:
    """Return (folder, is_demo).

    Order of preference:
      1. the folder named in the PRODUCTPULSE_DATA environment variable
      2. data/exports  (real BigQuery exports)
      3. data/demo     (synthetic demo data)
    """
    override = os.environ.get("PRODUCTPULSE_DATA")
    if override:
        folder = Path(override)
        return folder, folder.resolve() == DEMO_DIR.resolve()
    if all((EXPORT_DIR / f"{t}.csv").exists() for t in REQUIRED_TABLES):
        return EXPORT_DIR, False
    if all((DEMO_DIR / f"{t}.csv").exists() for t in REQUIRED_TABLES):
        return DEMO_DIR, True
    raise FileNotFoundError(
        "No data found. Run `python scripts/export_from_bigquery.py --project YOUR_PROJECT` "
        "for real data, or `python scripts/make_demo_data.py` for synthetic demo data."
    )


def data_banner() -> str:
    """One line that says which data is loaded. Print it at the top of every notebook."""
    folder, is_demo = get_data_dir()
    if is_demo:
        return (
            "WARNING: SYNTHETIC DEMO DATA is loaded (data/demo). "
            "These numbers are made up to test the code. They are NOT findings. "
            "Run scripts/export_from_bigquery.py to load the real GA4 sample."
        )
    return f"Real BigQuery export loaded from: {folder}"


def load(name: str) -> pd.DataFrame:
    """Load one exported table by name, e.g. load('daily_metrics')."""
    folder, _ = get_data_dir()
    path = folder / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Re-run the export script.")
    df = pd.read_csv(path, dtype={"user_pseudo_id": "string", "transaction_id": "string"})
    for col in DATE_COLUMNS.get(name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


def load_model() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (fact_user_day, dim_user).

    fact_user_day : one row per user per active day
    dim_user      : one row per user (device, country, channel, cohort)
    """
    return load("fact_user_day"), load("dim_user")


def fact_with_dims(fact: pd.DataFrame, dim: pd.DataFrame) -> pd.DataFrame:
    """Attach the user attributes to every fact row (many-to-one join)."""
    cols = ["user_pseudo_id", "device_category", "country", "channel_group",
            "first_user_source", "first_user_medium", "cohort_month", "first_seen_dt"]
    merged = fact.merge(dim[cols], on="user_pseudo_id", how="left", validate="many_to_one")
    assert len(merged) == len(fact), "Join changed the row count - dim_user is not unique per user."
    return merged
