"""Build the verified metric summary that the AI insight workflow is allowed to see.

Reads the exported tables and writes:
  ai/verified_metrics.json   (or ai/verified_metrics.DEMO.json for synthetic data)
  reports/kpi_snapshot.md    (the same numbers as a readable table)

Every metric carries its numerator, denominator, unit, segment, definition,
SQL reference and caveat, so each sentence an assistant writes can be traced.

Usage:  python scripts/build_metric_summary.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from productpulse import data, metrics  # noqa: E402


def pct(x) -> str:
    return "n/a" if x != x else f"{x:.2%}"


def metric(id_, group, name, value, formatted, numerator, denominator, unit, segment, definition, sql, caveat):
    return {"id": id_, "group": group, "name": name, "value": value, "value_formatted": formatted,
            "numerator": numerator, "denominator": denominator, "unit": unit, "segment": segment,
            "definition": definition, "sql_reference": sql, "caveat": caveat}


def rate_metric(id_, group, name, num, den, num_label, den_label, unit, segment, definition, sql, caveat):
    value = metrics.safe_div(num, den)
    return metric(id_, group, name, None if value != value else round(value, 6), pct(value),
                  f"{num:,} {num_label}", f"{den:,} {den_label}", unit, segment, definition, sql, caveat)


def main() -> None:
    folder, is_demo = data.get_data_dir()
    fact, dim = data.load_model()
    fd = data.fact_with_dims(fact, dim)
    start, end = fact["event_dt"].min().date(), fact["event_dt"].max().date()
    out = []

    # ---- Headline -----------------------------------------------------
    k = metrics.headline_kpis(fact)
    out.append(metric("active_users", "headline", "Active users", k["active_users"], f"{k['active_users']:,}",
                      None, None, "user", "All users",
                      "Distinct user_pseudo_id with at least one event in the period.",
                      "sql/03_event_metrics.sql Q14-Q15", "Pseudonymous browser/device ids, not people."))
    out.append(rate_metric("user_purchase_conversion", "headline", "User purchase conversion",
                           k["purchasers"], k["active_users"], "users with a purchase event", "active users",
                           "user", "All users",
                           "Users with at least one purchase event divided by active users, same period.",
                           "sql/04_funnel_analysis.sql Q19", "Stage presence over the whole period, not per session."))
    out.append(metric("validated_orders", "headline", "Validated orders", k["orders"], f"{k['orders']:,}",
                      None, None, "order", "All users",
                      "Distinct transaction_id that is not null and not '(not set)'.",
                      "sql/02_data_quality.sql Q11", "Purchase events without a usable transaction id are excluded."))
    out.append(metric("revenue_usd", "headline", "Revenue (USD, de-duplicated)", k["revenue_usd"],
                      f"${k['revenue_usd']:,.2f}", None, f"{k['orders']:,} validated orders", "order",
                      "All users", "Sum of purchase_revenue_in_usd, counted once per transaction_id.",
                      "sql/02_data_quality.sql Q11", "Obfuscated sample; not the store's real revenue."))

    # ---- User-level funnel -------------------------------------------
    f = metrics.user_funnel(fact)
    users = dict(zip(f["stage"], f["users"]))
    steps = [("View item", "Add to cart", "view_to_cart"), ("Add to cart", "Begin checkout", "cart_to_checkout"),
             ("Begin checkout", "Purchase", "checkout_to_purchase"), ("View item", "Purchase", "view_to_purchase")]
    for a, b, key in steps:
        out.append(rate_metric(f"funnel_user_{key}", "funnel", f"User funnel: {a} to {b}",
                               users[b], users[a], f"users with '{b}'", f"users with '{a}'", "user", "All users",
                               "User-level stage-presence funnel: each event at least once, any order, whole period.",
                               "sql/04_funnel_analysis.sql Q19", "Not sequential; does not prove order of events."))
    worst = metrics.largest_drop_off(f)
    out.append(metric("funnel_user_largest_drop_off", "funnel", "User funnel: largest step drop-off",
                      round(worst["drop_off_rate"], 6), pct(worst["drop_off_rate"]),
                      f"{worst['from_count'] - worst['to_count']:,} users not reaching '{worst['to_stage']}'",
                      f"{worst['from_count']:,} users with '{worst['from_stage']}'", "user",
                      f"{worst['from_stage']} to {worst['to_stage']}",
                      "1 minus step conversion, for the step with the highest drop-off rate.",
                      "sql/04_funnel_analysis.sql Q19", "Stage presence, not sequence."))

    # ---- Sequential session funnel -------------------------------------
    sf = data.load("session_funnel")
    t = metrics.session_funnel_table(sf).iloc[0]
    for a, b, key, na, nb in [("View item", "Add to cart", "view_to_cart", "seq_view", "seq_cart"),
                              ("Add to cart", "Begin checkout", "cart_to_checkout", "seq_cart", "seq_checkout"),
                              ("Begin checkout", "Purchase", "checkout_to_purchase", "seq_checkout", "seq_purchase")]:
        out.append(rate_metric(f"funnel_session_{key}", "funnel", f"Session funnel (sequential): {a} to {b}",
                               int(t[nb]), int(t[na]), f"sessions reaching '{b}' in order",
                               f"sessions reaching '{a}' in order", "session", "All sessions",
                               "Sequential funnel inside one session: each stage at or after the previous one.",
                               "sql/04_funnel_analysis.sql Q21", "Purchases completing a cart from an earlier session are not counted."))

    # ---- Device --------------------------------------------------------
    by_dev = metrics.user_funnel_by(fd, "device_category")
    for _, r in by_dev.iterrows():
        dev = r["device_category"]
        out.append(rate_metric(f"device_{dev}_purchase_conversion", "device", f"User purchase conversion: {dev}",
                               int(r["users_purchased"]), int(r["users"]), "users with a purchase", "users",
                               "user", f"device = {dev}", "Purchasers divided by users whose first observed device is this one.",
                               "sql/04_funnel_analysis.sql Q20", "Device is the first observed device per user."))
        out.append(rate_metric(f"device_{dev}_view_to_cart", "device", f"View item to add to cart: {dev}",
                               int(r["users_added_cart"]), int(r["users_viewed"]), "users who added to cart",
                               "users who viewed an item", "user", f"device = {dev}",
                               "Stage-presence step conversion by first observed device.",
                               "sql/04_funnel_analysis.sql Q20", "Small devices (tablet) give unstable rates."))
        out.append(rate_metric(f"device_{dev}_cart_to_checkout", "device", f"Add to cart to begin checkout: {dev}",
                               int(r["users_began_checkout"]), int(r["users_added_cart"]), "users who began checkout",
                               "users who added to cart", "user", f"device = {dev}",
                               "Stage-presence step conversion by first observed device.",
                               "sql/04_funnel_analysis.sql Q20", "Small devices (tablet) give unstable rates."))

    # ---- Channel -------------------------------------------------------
    by_ch = metrics.user_funnel_by(fd, "channel_group")
    for _, r in by_ch.iterrows():
        ch = r["channel_group"]
        key = ch.lower().replace(" ", "_")
        out.append(rate_metric(f"channel_{key}_purchase_conversion", "channel", f"User purchase conversion: {ch}",
                               int(r["users_purchased"]), int(r["users"]), "users with a purchase", "users",
                               "user", f"channel = {ch}", "Purchasers divided by users first acquired through this channel.",
                               "sql/07_segment_analysis.sql Q31",
                               "First-touch, user-level attribution. 'Other' and 'Data deleted' are obfuscation artefacts."))

    # ---- Cohorts -------------------------------------------------------
    coh = metrics.cohort_retention(fact, dim)
    last_month = fact["event_dt"].max().to_period("M")
    for _, r in coh[coh["month_number"] > 0].iterrows():
        label = r["cohort_month"].strftime("%Y-%m")
        out.append(rate_metric(f"retention_{label}_month_{int(r['month_number'])}", "retention",
                               f"Activity retention: {label} cohort, month {int(r['month_number'])}",
                               int(r["active_users"]), int(r["cohort_users"]), "cohort users active in that month",
                               "users in cohort", "user", f"cohort = {label}",
                               "Share of users first observed in the cohort month with any event N months later.",
                               "sql/05_cohort_retention.sql Q23",
                               "First OBSERVED activity, not true first visit. The sample has only three months."))
    feats = metrics.engagement_features(fact, dim)
    one_day = int((feats["active_days"] == 1).sum())
    out.append(rate_metric("single_day_users", "retention", "Users active on one day only", one_day, len(feats),
                           "users with exactly one active day", "users", "user", "All users",
                           "Users whose events all fall on a single calendar day in the sample.",
                           "sql/05_cohort_retention.sql Q25", "Late arrivals have had less time to return."))

    # ---- Products ------------------------------------------------------
    prod = data.load("product_performance").head(5)
    for i, r in enumerate(prod.itertuples(), start=1):
        out.append(rate_metric(f"product_top{i}_viewer_to_buyer", "product", f"Viewer-to-buyer rate: {r.item_name}",
                               int(r.users_purchased), int(r.users_viewed), "users who bought the item",
                               "users who viewed the item", "user", f"item = {r.item_name} (#{i} by viewers)",
                               "Users who purchased the item divided by users who viewed it, whole period.",
                               "sql/06_product_analysis.sql Q27", "Association only: the view need not precede the purchase."))

    summary = {
        "data_source": ("SYNTHETIC DEMO DATA - not findings" if is_demo else
                        "bigquery-public-data.ga4_obfuscated_sample_ecommerce (exported aggregates)"),
        "is_demo": is_demo,
        "generated_on": date.today().isoformat(),
        "reporting_period": {"start": str(start), "end": str(end)},
        "notes": ["Aggregates only. No raw events and no user identifiers.",
                  "All user metrics exclude rows with a null user_pseudo_id."],
        "metrics": out,
    }
    target = ROOT / "ai" / ("verified_metrics.DEMO.json" if is_demo else "verified_metrics.json")
    target.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [f"# KPI snapshot{' (SYNTHETIC DEMO DATA - not findings)' if is_demo else ''}", "",
             f"Reporting period: {start} to {end}  ", f"Source: {summary['data_source']}  ",
             f"Generated: {summary['generated_on']} by `scripts/build_metric_summary.py`", "",
             "| Metric id | Metric | Value | Numerator | Denominator | Segment | SQL |",
             "|---|---|---|---|---|---|---|"]
    for m in out:
        lines.append(f"| `{m['id']}` | {m['name']} | **{m['value_formatted']}** | {m['numerator'] or ''} | "
                     f"{m['denominator'] or ''} | {m['segment']} | {m['sql_reference']} |")
    snap = ROOT / "reports" / ("kpi_snapshot.DEMO.md" if is_demo else "kpi_snapshot.md")
    snap.parent.mkdir(exist_ok=True)
    snap.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(data.data_banner())
    print(f"Wrote {target.relative_to(ROOT)} ({len(out)} metrics) and {snap.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
