"""Create SYNTHETIC demo data in data/demo/.

Why this exists
---------------
The real analysis needs your own BigQuery export (scripts/export_from_bigquery.py).
Until you have run that, this script produces small made-up tables with the SAME
file names and columns, so you can check that the notebooks and the Streamlit app
run on your computer.

Everything written here is random and invented (fixed seed 7). It is NOT the GA4
sample and must never be quoted as a finding.

Usage:  python scripts/make_demo_data.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "demo"
SEED = 7
N_USERS = 12_000
START = pd.Timestamp("2020-11-01")
END = pd.Timestamp("2021-01-31")

CHANNELS = [  # (source, medium, channel_group, weight)
    ("google", "organic", "Organic search", 0.34),
    ("(direct)", "(none)", "Direct", 0.23),
    ("<Other>", "<Other>", "Other", 0.17),
    ("shop.demo-referrer.example", "referral", "Referral", 0.12),
    ("google", "cpc", "Paid search", 0.06),
    ("(data deleted)", "(data deleted)", "Data deleted", 0.08),
]
DEVICES = [("desktop", 0.58), ("mobile", 0.40), ("tablet", 0.02)]
COUNTRIES = [("United States", 0.44), ("India", 0.09), ("Canada", 0.08), ("United Kingdom", 0.05),
             ("Germany", 0.04), ("Japan", 0.03), ("France", 0.03), ("Spain", 0.03),
             ("Australia", 0.02), ("(not set)", 0.01), ("Other demo countries", 0.18)]
ITEMS = [(f"Demo Item {i:02d}", cat, price) for i, (cat, price) in enumerate([
    ("Apparel", 24.0), ("Apparel", 32.0), ("Apparel", 18.0), ("Apparel", 45.0), ("Apparel", 28.0),
    ("Bags", 55.0), ("Bags", 38.0), ("Drinkware", 14.0), ("Drinkware", 20.0), ("Drinkware", 16.0),
    ("Office", 6.0), ("Office", 9.0), ("Office", 12.0), ("Accessories", 8.0), ("Accessories", 15.0),
    ("Lifestyle", 22.0), ("Lifestyle", 30.0), ("Campus", 26.0), ("Campus", 19.0), ("Clearance", 10.0),
], start=1)]


def pick(rng, options):
    weights = np.array([o[-1] for o in options], dtype=float)
    return options[rng.choice(len(options), p=weights / weights.sum())]


def simulate_events(rng) -> pd.DataFrame:
    """Build a synthetic event table shaped like the events_base view."""
    n_days = (END - START).days + 1
    rows = []
    tx_counter = 0
    item_pop = np.array([1 / (i + 1) ** 0.6 for i in range(len(ITEMS))])
    item_pop /= item_pop.sum()
    for u in range(N_USERS):
        uid = f"demo{u:07d}.{rng.integers(1_000_000_000, 9_999_999_999)}"
        device = pick(rng, DEVICES)[0]
        country = pick(rng, COUNTRIES)[0]
        source, medium, channel, _ = pick(rng, CHANNELS)
        first_day = int(rng.integers(0, n_days))
        # Most users are seen on one day only; a few return.
        extra_days = rng.geometric(0.72) - 1
        offsets = {0}
        for _ in range(extra_days):
            offsets.add(int(rng.exponential(12)) + 1)
        days = sorted(first_day + o for o in offsets if first_day + o < n_days)
        session_number = 0
        base_view = {"desktop": 0.27, "mobile": 0.22, "tablet": 0.20}[device]
        for d in days:
            for _ in range(1 + int(rng.random() < 0.15)):
                session_number += 1
                ts = int((START + pd.Timedelta(days=d)).value // 1000) + int(rng.integers(0, 86_000)) * 1_000_000
                sid = ts // 1_000_000

                def add(name, t, **kw):
                    rows.append({"user_pseudo_id": uid, "event_dt": START + pd.Timedelta(days=d),
                                 "event_timestamp": t, "event_name": name, "ga_session_id": sid,
                                 "device_category": device, "country": country,
                                 "first_user_source": source, "first_user_medium": medium,
                                 "channel_group": channel,
                                 "engagement_time_msec": int(rng.integers(0, 40_000)), **kw})

                add("session_start", ts)
                t = ts
                for _ in range(int(rng.integers(1, 6))):
                    t += int(rng.integers(2, 90)) * 1_000_000
                    add("page_view", t)
                    if rng.random() < 0.5:
                        add("user_engagement", t + 500_000)
                returning_boost = 1.5 if session_number > 1 else 1.0
                if rng.random() < base_view * returning_boost:
                    item = ITEMS[rng.choice(len(ITEMS), p=item_pop)]
                    t += int(rng.integers(5, 120)) * 1_000_000
                    add("view_item", t, item_name=item[0], item_category=item[1])
                    if rng.random() < 0.21:
                        t += int(rng.integers(5, 200)) * 1_000_000
                        add("add_to_cart", t, item_name=item[0], item_category=item[1])
                        p_checkout = {"desktop": 0.50, "mobile": 0.38, "tablet": 0.40}[device]
                        if rng.random() < p_checkout:
                            t += int(rng.integers(10, 300)) * 1_000_000
                            add("begin_checkout", t, item_name=item[0], item_category=item[1])
                            if rng.random() < 0.46:
                                t += int(rng.integers(30, 600)) * 1_000_000
                                qty = int(rng.integers(1, 4))
                                tx_counter += 1
                                revenue = round(item[2] * qty, 2)
                                tx_id = None if rng.random() < 0.02 else f"DEMO{tx_counter:06d}"
                                add("purchase", t, item_name=item[0], item_category=item[1],
                                    transaction_id=tx_id, purchase_revenue_usd=revenue,
                                    quantity=qty, item_revenue_in_usd=revenue)
                                if tx_id and rng.random() < 0.03:   # a repeated purchase event
                                    add("purchase", t + 2_000_000, item_name=item[0],
                                        item_category=item[1], transaction_id=tx_id,
                                        purchase_revenue_usd=revenue, quantity=qty,
                                        item_revenue_in_usd=revenue)
    ev = pd.DataFrame(rows)
    for col in ["item_name", "item_category", "transaction_id"]:
        ev[col] = ev[col].astype("object")
    return ev


def valid_tx(ev: pd.DataFrame) -> pd.DataFrame:
    p = ev[(ev["event_name"] == "purchase") & ev["transaction_id"].notna()]
    return p


def build_exports(ev: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Derive every export table from the synthetic events (mirrors sql/exports/*.sql)."""
    out = {}
    ev = ev.sort_values(["user_pseudo_id", "event_timestamp", "event_name"]).reset_index(drop=True)
    ev["session_key"] = ev["user_pseudo_id"] + "-" + ev["ga_session_id"].astype(str)
    for stage, name in [("viewed_item", "view_item"), ("added_cart", "add_to_cart"),
                        ("began_checkout", "begin_checkout"), ("purchased", "purchase")]:
        ev[stage] = (ev["event_name"] == name).astype(int)

    out["dataset_overview"] = pd.DataFrame([{
        "first_event_date": ev["event_dt"].min().date(), "last_event_date": ev["event_dt"].max().date(),
        "days_with_data": ev["event_dt"].nunique(), "event_rows": len(ev),
        "identified_users": ev["user_pseudo_id"].nunique(), "null_user_id_rows": 0,
        "null_session_id_rows": 0, "sessions": ev["session_key"].nunique(),
        "distinct_event_names": ev["event_name"].nunique()}])

    out["event_overview"] = (ev.groupby("event_name").agg(event_rows=("event_name", "size"),
                             users=("user_pseudo_id", "nunique")).reset_index()
                             .sort_values("event_rows", ascending=False))

    out["event_param_keys"] = pd.DataFrame([
        {"key": "ga_session_id", "occurrences": len(ev), "string_values": 0, "int_values": len(ev),
         "float_values": 0, "double_values": 0},
        {"key": "engagement_time_msec", "occurrences": len(ev), "string_values": 0,
         "int_values": len(ev), "float_values": 0, "double_values": 0}])

    tx = (valid_tx(ev).groupby("transaction_id").agg(
        user_pseudo_id=("user_pseudo_id", "first"), event_dt=("event_dt", "min"),
        device_category=("device_category", "min"), purchase_events=("event_name", "size"),
        distinct_users=("user_pseudo_id", "nunique"), revenue_usd=("purchase_revenue_usd", "max"),
        min_revenue_usd=("purchase_revenue_usd", "min"), total_item_quantity=("quantity", "max"))
        .reset_index())

    daily = ev.groupby("event_dt").agg(total_events=("event_name", "size"),
                                       active_users=("user_pseudo_id", "nunique"),
                                       sessions=("session_key", "nunique"))
    daily["purchasers"] = ev[ev["purchased"] == 1].groupby("event_dt")["user_pseudo_id"].nunique()
    dtx = tx.groupby("event_dt").agg(transactions=("transaction_id", "size"),
                                     revenue_usd=("revenue_usd", "sum"))
    daily = daily.join(dtx).fillna(0)
    daily[["purchasers", "transactions"]] = daily[["purchasers", "transactions"]].astype(int)
    daily["revenue_usd"] = daily["revenue_usd"].round(2)
    out["daily_metrics"] = daily.reset_index()

    first = ev.drop_duplicates("user_pseudo_id", keep="first").set_index("user_pseudo_id")
    span = ev.groupby("user_pseudo_id").agg(first_seen_dt=("event_dt", "min"),
                                            last_seen_dt=("event_dt", "max"),
                                            n_devices=("device_category", "nunique"))
    dim = span.join(first[["device_category", "country", "first_user_source",
                           "first_user_medium", "channel_group"]])
    dim["cohort_month"] = dim["first_seen_dt"].dt.to_period("M").dt.to_timestamp()
    out["dim_user"] = dim.reset_index()[[
        "user_pseudo_id", "first_seen_dt", "last_seen_dt", "cohort_month", "device_category",
        "country", "first_user_source", "first_user_medium", "channel_group", "n_devices"]]

    fact = ev.groupby(["user_pseudo_id", "event_dt"]).agg(
        events=("event_name", "size"), sessions=("ga_session_id", "nunique"),
        page_views=("event_name", lambda s: int((s == "page_view").sum())),
        engagement_sec=("engagement_time_msec", lambda s: round(s.sum() / 1000, 1)),
        viewed_item=("viewed_item", "max"), added_cart=("added_cart", "max"),
        began_checkout=("began_checkout", "max"), purchased=("purchased", "max")).reset_index()
    utx = tx.groupby(["user_pseudo_id", "event_dt"]).agg(
        transactions=("transaction_id", "size"), revenue_usd=("revenue_usd", "sum")).reset_index()
    fact = fact.merge(utx, on=["user_pseudo_id", "event_dt"], how="left")
    fact["transactions"] = fact["transactions"].fillna(0).astype(int)
    fact["revenue_usd"] = fact["revenue_usd"].fillna(0).round(2)
    out["fact_user_day"] = fact

    flags = ev.groupby("user_pseudo_id")[["viewed_item", "added_cart", "began_checkout", "purchased"]].max()
    flags = flags.join(first["device_category"])
    out["user_funnel_by_device"] = flags.groupby("device_category").agg(
        users=("viewed_item", "size"), users_viewed=("viewed_item", "sum"),
        users_added_cart=("added_cart", "sum"), users_began_checkout=("began_checkout", "sum"),
        users_purchased=("purchased", "sum")).reset_index().sort_values("users", ascending=False)

    # Sequential session funnel
    def first_after(frame, name, after_col):
        mask = frame["event_name"] == name
        if after_col:
            mask &= frame["event_timestamp"] >= frame[after_col]
        return frame["event_timestamp"].where(mask).groupby(frame["session_key"]).transform("min")
    ev["t_view"] = first_after(ev, "view_item", None)
    ev["t_cart"] = first_after(ev, "add_to_cart", "t_view")
    ev["t_checkout"] = first_after(ev, "begin_checkout", "t_cart")
    ev["t_purchase"] = first_after(ev, "purchase", "t_checkout")
    sess = ev.groupby("session_key").agg(
        device_category=("device_category", "min"), channel_group=("channel_group", "min"),
        t_view=("t_view", "max"), t_cart=("t_cart", "max"), t_checkout=("t_checkout", "max"),
        t_purchase=("t_purchase", "max"), any_purchase=("purchased", "max"))
    out["session_funnel"] = sess.groupby(["device_category", "channel_group"]).agg(
        sessions=("any_purchase", "size"), seq_view=("t_view", "count"), seq_cart=("t_cart", "count"),
        seq_checkout=("t_checkout", "count"), seq_purchase=("t_purchase", "count"),
        any_purchase=("any_purchase", "sum")).reset_index().sort_values("sessions", ascending=False)

    # Monthly cohort retention, computed straight from events (independent of metrics.py)
    um = ev[["user_pseudo_id", "event_dt"]].copy()
    um["activity_month"] = um["event_dt"].dt.to_period("M")
    um = um.drop_duplicates(["user_pseudo_id", "activity_month"])
    um["cohort"] = um.groupby("user_pseudo_id")["activity_month"].transform("min")
    um["month_number"] = [(a.year - c.year) * 12 + a.month - c.month
                          for a, c in zip(um["activity_month"], um["cohort"])]
    coh = um.groupby(["cohort", "month_number"])["user_pseudo_id"].nunique().rename("active_users").reset_index()
    size = coh[coh["month_number"] == 0].set_index("cohort")["active_users"]
    coh["cohort_users"] = coh["cohort"].map(size)
    coh["retention_rate"] = (coh["active_users"] / coh["cohort_users"]).round(4)
    coh["cohort_month"] = coh["cohort"].dt.to_timestamp()
    out["cohort_retention_monthly"] = coh[["cohort_month", "month_number", "active_users",
                                           "cohort_users", "retention_rate"]]

    items = ev[ev["item_name"].notna()]
    def users_where(name):
        return items[items["event_name"] == name].groupby("item_name")["user_pseudo_id"].nunique()
    purchases = items[items["event_name"] == "purchase"]
    prod = pd.DataFrame({
        "item_category": items.groupby("item_name")["item_category"].first(),
        "users_viewed": users_where("view_item"),
        "users_added_cart": users_where("add_to_cart"),
        "users_purchased": users_where("purchase"),
        "orders": purchases.groupby("item_name")["transaction_id"].nunique(),
        "units_purchased": purchases.groupby("item_name")["quantity"].sum(),
        "item_revenue_usd": purchases.groupby("item_name")["item_revenue_in_usd"].sum().round(2),
    }).fillna(0).reset_index().rename(columns={"index": "item_name"})
    for c in ["users_viewed", "users_added_cart", "users_purchased", "orders", "units_purchased"]:
        prod[c] = prod[c].astype(int)
    out["product_performance"] = prod.sort_values("users_viewed", ascending=False)

    out["transactions"] = tx.rename(columns={"event_dt": "purchase_dt"})[[
        "transaction_id", "purchase_dt", "device_category", "purchase_events", "distinct_users",
        "revenue_usd", "min_revenue_usd", "total_item_quantity"]]

    p = ev[ev["event_name"] == "purchase"]
    dup = ev.groupby(["user_pseudo_id", "event_timestamp", "event_name", "ga_session_id"]).size()
    out["data_quality"] = pd.DataFrame([
        ("event_rows", len(ev), "All rows in events_base"),
        ("null_user_id_rows", 0, "Excluded from user metrics"),
        ("null_session_id_rows", 0, "Excluded from session metrics"),
        ("null_device_rows", 0, "Shown as (not set)"),
        ("not_set_country_rows", int((ev["country"] == "(not set)").sum()), "Shown as (not set)"),
        ("data_deleted_source_rows", int((ev["first_user_source"] == "(data deleted)").sum()),
         "Obfuscation artefact; channel = Data deleted"),
        ("other_source_rows", int((ev["first_user_source"] == "<Other>").sum()),
         "Obfuscation artefact; channel = Other"),
        ("utc_date_differs_rows", 0, "event_date is property time zone, timestamp is UTC"),
        ("duplicate_extra_copies", int((dup - 1).sum()), "Same user, microsecond, event and session; reported, not removed"),
        ("purchase_events", len(p), "Rows with event_name = purchase"),
        ("purchase_null_or_not_set_transaction_id", int(p["transaction_id"].isna().sum()),
         "Excluded from validated orders"),
        ("purchase_null_revenue", int(p["purchase_revenue_usd"].isna().sum()), "Treated as 0 revenue"),
        ("validated_orders", len(tx), "Distinct valid transaction_id"),
        ("orders_with_repeat_purchase_events", int((tx["purchase_events"] > 1).sum()),
         "Reason revenue is de-duplicated"),
        ("revenue_summing_every_event_usd", round(float(p["purchase_revenue_usd"].sum()), 2),
         "NOT used: may double count"),
        ("revenue_deduplicated_usd", round(float(tx["revenue_usd"].sum()), 2),
         "Used everywhere in this project"),
    ], columns=["check_name", "value", "note"])
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    events = simulate_events(rng)
    tables = build_exports(events)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"  wrote data/demo/{name}.csv  ({len(df):,} rows)")
    (OUT / "README_SYNTHETIC.txt").write_text(
        "SYNTHETIC DEMO DATA - NOT THE GA4 SAMPLE.\n"
        "Created by scripts/make_demo_data.py with a fixed random seed.\n"
        "Use only to test that the code runs. Never quote these numbers as findings.\n",
        encoding="utf-8")
    print("Done. These files are synthetic. Do not report numbers from them.")


if __name__ == "__main__":
    main()
