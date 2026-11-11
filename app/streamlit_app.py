"""ProductPulse AI - Streamlit report (optional web front end).

Run from the project folder:
    streamlit run app/streamlit_app.py

It mirrors the four Power BI pages and adds an "Ask about this report" panel.
All numbers come from the exported aggregates; the AI panel only ever sees
ai/verified_metrics.json.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from productpulse import charts, data, insights, metrics  # noqa: E402

st.set_page_config(page_title="ProductPulse AI", page_icon=":bar_chart:", layout="wide")
charts.apply_style()

st.markdown("""
<style>
  .stApp { background-color: #F5F7FB; }
  h1, h2, h3 { color: #14243A; }
  div[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E2E8F0;
                                border-radius: 8px; padding: 16px; }
  .pp-note { color: #64748B; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_all():
    fact, dim = data.load_model()
    return {
        "fd": data.fact_with_dims(fact, dim),
        "dim": dim,
        "session_funnel": data.load("session_funnel"),
        "products": data.load("product_performance"),
        "is_demo": data.get_data_dir()[1],
    }


def show(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def pct(x):
    return "n/a" if x != x else f"{x:.2%}"


tables = load_all()
fd_all, dim_all = tables["fd"], tables["dim"]
min_day, max_day = fd_all["event_dt"].min().date(), fd_all["event_dt"].max().date()

# ----------------------------------------------------------------- sidebar
st.sidebar.title("ProductPulse AI")
st.sidebar.caption("Filters apply to every page unless a page says otherwise.")
picked = st.sidebar.date_input("Date range", value=(min_day, max_day), min_value=min_day, max_value=max_day)
start, end = (picked if isinstance(picked, (tuple, list)) and len(picked) == 2 else (min_day, max_day))
devices = st.sidebar.multiselect("Device (first observed)", sorted(dim_all["device_category"].unique()))
channels = st.sidebar.multiselect("Channel (first touch)", sorted(dim_all["channel_group"].unique()))
top_countries = dim_all["country"].value_counts().head(25).index.tolist()
countries = st.sidebar.multiselect("Country (top 25 by users)", top_countries)
st.sidebar.caption("Leave a filter empty to include everything. To reset, clear the boxes.")

fd = metrics.filter_fact(fd_all, start, end, devices, countries, channels)
dim = dim_all
for column, chosen in [("device_category", devices), ("channel_group", channels), ("country", countries)]:
    if chosen:
        dim = dim[dim[column].isin(chosen)]
session_funnel = tables["session_funnel"]
if devices:
    session_funnel = session_funnel[session_funnel["device_category"].isin(devices)]
if channels:
    session_funnel = session_funnel[session_funnel["channel_group"].isin(channels)]

period = f"{start} to {end}"
filters_text = "; ".join(f"{name}: {', '.join(v)}" for name, v in
                         [("device", devices), ("channel", channels), ("country", countries)] if v) or "no segment filters"

# ------------------------------------------------------------------ header
st.title("ProductPulse AI")
st.caption(f"Product analytics and retention report | GA4 obfuscated ecommerce sample | {period} | {filters_text}")
if tables["is_demo"]:
    st.warning("SYNTHETIC DEMO DATA is loaded. These numbers are invented to test the app and are not findings. "
               "Run scripts/export_from_bigquery.py to load the real GA4 sample.")
if fd.empty:
    st.error("No data for this filter combination. Widen the filters.")
    st.stop()

overview, funnel_tab, retention_tab, product_tab, ask_tab = st.tabs(
    ["Executive overview", "Conversion funnel", "Retention and cohorts", "Products and acquisition",
     "Ask about this report"])

# ------------------------------------------------------- 1. overview page
with overview:
    k = metrics.headline_kpis(fd)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active users", f"{k['active_users']:,}", help="Distinct user_pseudo_id with any event in the selection.")
    c2.metric("Validated orders", f"{k['orders']:,}", help="Distinct transaction_id that is not null and not '(not set)'.")
    c3.metric("User purchase conversion", pct(k["purchase_conversion"]),
              help=f"{k['purchasers']:,} users with a purchase / {k['active_users']:,} active users.")
    c4.metric("Revenue (USD)", f"${k['revenue_usd']:,.0f}", help="purchase_revenue_in_usd, counted once per order.")

    trend = metrics.daily_trend(fd)
    fig, _ = charts.line_chart(trend, "event_dt", "active_users", "Daily active users", "Distinct users", rolling=7)
    show(fig)
    fig, _ = charts.line_chart(trend, "event_dt", "purchase_conversion", "Daily user purchase conversion",
                               "Purchasers / active users", percent=True, rolling=7)
    show(fig)
    st.markdown('<p class="pp-note">Two charts instead of one dual-axis chart, so each line has its own honest scale.</p>',
                unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        mix = fd.groupby("device_category")["user_pseudo_id"].nunique().sort_values(ascending=False)
        fig, _ = charts.bar_chart(mix.index, mix.values, "Active users by device", "Users",
                                  colours=[charts.DEVICE_COLOURS.get(d, charts.BLUE) for d in mix.index])
        show(fig)
    with right:
        by_channel = metrics.user_funnel_by(fd, "channel_group")
        fig, _ = charts.bar_chart(by_channel["channel_group"], by_channel["user_purchase_conversion"],
                                  "User purchase conversion by channel", "Purchasers / users", percent=True)
        show(fig)

    worst = metrics.largest_drop_off(metrics.user_funnel(fd))
    st.info(f"**Verified observation:** the largest step drop-off in the user-level funnel is "
            f"**{worst['from_stage']} to {worst['to_stage']}**: {worst['drop_off_rate']:.1%} of "
            f"{worst['from_count']:,} users did not continue ({period}; {filters_text}).  \n"
            f"**To investigate (unproven):** whether this step differs by device or channel. See the *Conversion funnel* tab.")

# --------------------------------------------------------- 2. funnel page
with funnel_tab:
    st.subheader("User-level funnel (stage presence)")
    st.caption("Unit: users. A stage counts if the user fired the event at least once in the selection, in any order.")
    funnel = metrics.user_funnel(fd)
    fig, _ = charts.funnel_chart(funnel, "users", "View item to purchase: users reaching each stage", "Users")
    show(fig)
    st.dataframe(funnel.style.format({"users": "{:,.0f}", "pct_of_first_stage": "{:.1%}", "step_conversion": "{:.1%}",
                                      "drop_off_users": "{:,.0f}", "drop_off_rate": "{:.1%}"}, na_rep="-"),
                 use_container_width=True, hide_index=True)

    breakdown = st.radio("Break down by", ["device_category", "channel_group", "country"], horizontal=True,
                         format_func=lambda c: {"device_category": "Device", "channel_group": "Channel", "country": "Country"}[c])
    seg = metrics.user_funnel_by(fd, breakdown).head(10)
    rate_cols = {"view_to_cart_rate": "View -> cart", "cart_to_checkout_rate": "Cart -> checkout",
                 "checkout_to_purchase_rate": "Checkout -> purchase"}
    fig, _ = charts.grouped_rate_chart(seg, breakdown, rate_cols, "Step conversion by segment (top 10 by users)")
    show(fig)
    st.dataframe(seg.style.format({c: "{:.1%}" for c in seg.columns if c.endswith("_rate") or c.endswith("_conversion")}
                                  | {c: "{:,.0f}" for c in seg.columns if c.startswith("users")}, na_rep="-"),
                 use_container_width=True, hide_index=True)

    st.subheader("Sequential session funnel")
    st.caption("Unit: sessions, whole sample period (the date and country filters do not apply to this table). "
               "A stage counts only if it happened at or after the previous stage inside the same session.")
    seq = metrics.session_funnel_long(session_funnel)
    fig, _ = charts.funnel_chart(seq, "sessions", "Sessions reaching each stage in order", "Sessions")
    show(fig)

# ------------------------------------------------------ 3. retention page
with retention_tab:
    st.subheader("Monthly activity retention by first-observed cohort")
    st.caption("Unit: users. Uses the whole sample period (the date filter is ignored so cohorts stay complete); "
               "device, channel and country filters apply. Blank cells were not observed: the sample ends 2021-01-31.")
    fact_cohort = fd_all[fd_all["user_pseudo_id"].isin(dim["user_pseudo_id"])]
    cohort = metrics.cohort_retention(fact_cohort, dim)
    matrix = metrics.cohort_matrix(cohort)
    sizes = cohort[cohort["month_number"] == 0].assign(
        label=lambda d: d["cohort_month"].dt.strftime("%Y-%m")).set_index("label")["cohort_users"]
    fig, _ = charts.cohort_heatmap(matrix, sizes, "Share of each cohort active N months later")
    show(fig)
    st.dataframe(cohort.assign(cohort_month=cohort["cohort_month"].dt.strftime("%Y-%m")).style.format(
        {"active_users": "{:,.0f}", "cohort_users": "{:,.0f}", "retention_rate": "{:.2%}"}),
        use_container_width=True, hide_index=True)

    per_user = fact_cohort.groupby("user_pseudo_id")["event_dt"].nunique()
    buckets = pd.cut(per_user, [0, 1, 2, 5, float("inf")], labels=["1 day only", "2 days", "3-5 days", "6+ days"])
    dist = buckets.value_counts().reindex(["1 day only", "2 days", "3-5 days", "6+ days"])
    fig, _ = charts.bar_chart(dist.index, dist.values, "Repeat activity: users by number of active days", "Users")
    show(fig)
    st.markdown('<p class="pp-note">First observed activity is not necessarily a user\'s first-ever visit. '
                'Retention here means any event, not a purchase.</p>', unsafe_allow_html=True)

# ------------------------------------------------------- 4. products page
with product_tab:
    st.subheader("Products")
    st.caption("Unit: users, whole sample period, all users (the sidebar filters do not apply to product tables). "
               "Viewer-to-buyer rate is an association: the view need not come before the purchase.")
    products = tables["products"].copy()
    products["viewer_to_buyer_rate"] = products["users_purchased"] / products["users_viewed"]
    left, right = st.columns(2)
    with left:
        top = products.nlargest(10, "users_viewed")
        fig, _ = charts.bar_chart(top["item_name"], top["users_viewed"], "Top 10 products by viewing users", "Users")
        show(fig)
    with right:
        top = products.nlargest(10, "item_revenue_usd")
        fig, _ = charts.bar_chart(top["item_name"], top["item_revenue_usd"], "Top 10 products by item revenue (USD)", "USD")
        show(fig)
    st.dataframe(products.style.format({"users_viewed": "{:,.0f}", "users_added_cart": "{:,.0f}",
                                        "users_purchased": "{:,.0f}", "orders": "{:,.0f}", "units_purchased": "{:,.0f}",
                                        "item_revenue_usd": "{:,.2f}", "viewer_to_buyer_rate": "{:.2%}"}, na_rep="-"),
                 use_container_width=True, hide_index=True)

    st.subheader("Acquisition")
    st.caption(f"Unit: users. {period}; {filters_text}. Channel is user-level first-touch attribution; "
               "'Other' and 'Data deleted' are obfuscation artefacts of the public sample.")
    acq = metrics.user_funnel_by(fd, "channel_group")
    revenue = fd.groupby("channel_group")["revenue_usd"].sum()
    acq["revenue_usd"] = acq["channel_group"].map(revenue)
    acq["revenue_per_user"] = acq["revenue_usd"] / acq["users"]
    st.dataframe(acq[["channel_group", "users", "users_viewed", "users_purchased", "user_purchase_conversion",
                      "revenue_usd", "revenue_per_user"]].style.format(
        {"users": "{:,.0f}", "users_viewed": "{:,.0f}", "users_purchased": "{:,.0f}",
         "user_purchase_conversion": "{:.2%}", "revenue_usd": "{:,.0f}", "revenue_per_user": "{:.2f}"}),
        use_container_width=True, hide_index=True)

# ------------------------------------------------------------ 5. AI panel
with ask_tab:
    st.subheader("Ask about this report")
    st.caption("Claude receives only the verified aggregate metrics in ai/verified_metrics.json, with their "
               "definitions and caveats. It never sees raw events or user ids. Every draft needs human review.")
    try:
        summary = insights.load_metrics()
    except FileNotFoundError:
        summary = None
        st.error("No metric summary found. Run: python scripts/build_metric_summary.py")

    if summary:
        if summary.get("is_demo"):
            st.warning("The metric summary was built from SYNTHETIC DEMO DATA.")
        st.markdown(f"**Source:** {summary['data_source']}  \n**Reporting period:** "
                    f"{summary['reporting_period']['start']} to {summary['reporting_period']['end']} "
                    f"(whole sample; sidebar filters do not apply here)")
        question_label = st.radio("Preset question", list(insights.PRESET_QUESTIONS))
        question = insights.PRESET_QUESTIONS[question_label]
        has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

        if st.button("Draft an answer with Claude", disabled=not has_key):
            try:
                with st.spinner("Asking Claude..."):
                    st.session_state["pp_answer"] = insights.ask_claude(summary, question)
                    st.session_state["pp_question"] = question_label
            except Exception as error:   # missing package, bad key, network...
                st.error(f"The request failed: {error}")
        if not has_key:
            st.info("No ANTHROPIC_API_KEY environment variable is set, so the live call is disabled. "
                    "Copy the prompt below into claude.ai instead, or see saved examples in ai/insight_validation.md.")

        if st.session_state.get("pp_answer"):
            st.markdown(f"#### Draft answer: {st.session_state['pp_question']}")
            st.markdown(st.session_state["pp_answer"])
            flagged = insights.find_unsupported_numbers(st.session_state["pp_answer"], summary)
            if flagged:
                st.warning("Numbers in the draft that were not found in the supplied metrics (check each): "
                           + ", ".join(flagged))
            else:
                st.success("Every number in the draft appears in the supplied metrics. Still check the wording.")
            st.caption("Unreviewed AI draft. Trace each sentence to a metric id below before using it.")

        with st.expander("Exact prompt sent to Claude"):
            st.code(insights.SYSTEM_PROMPT + "\n\n" + insights.build_prompt(summary, question), language="text")
        with st.expander("Source metrics (ids, values, denominators, SQL references)"):
            st.dataframe(pd.DataFrame(summary["metrics"])[
                ["id", "name", "value_formatted", "numerator", "denominator", "segment", "sql_reference", "caveat"]],
                use_container_width=True, hide_index=True)
