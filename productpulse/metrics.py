"""Reusable KPI calculations.

Every function states its unit of analysis. All "user" metrics count
DISTINCT user_pseudo_id inside whatever rows you pass in, so they stay
correct after filtering by date, device, country or channel.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

# Funnel stages: (flag column in fact_user_day, label)
STAGES = [
    ("viewed_item", "View item"),
    ("added_cart", "Add to cart"),
    ("began_checkout", "Begin checkout"),
    ("purchased", "Purchase"),
]
STAGE_COLUMNS = [c for c, _ in STAGES]
STAGE_LABELS = [label for _, label in STAGES]


def safe_div(numerator, denominator):
    """Divide, returning NaN instead of raising when the denominator is 0."""
    return numerator / denominator if denominator else float("nan")


# --------------------------------------------------------------------------
# Filtering
# --------------------------------------------------------------------------
def filter_fact(fact_dims: pd.DataFrame, start=None, end=None,
                devices=None, countries=None, channels=None) -> pd.DataFrame:
    """Filter the fact table (already joined to dim_user). None means "no filter"."""
    df = fact_dims
    if start is not None:
        df = df[df["event_dt"] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df["event_dt"] <= pd.Timestamp(end)]
    if devices:
        df = df[df["device_category"].isin(devices)]
    if countries:
        df = df[df["country"].isin(countries)]
    if channels:
        df = df[df["channel_group"].isin(channels)]
    return df


# --------------------------------------------------------------------------
# Headline KPIs
# --------------------------------------------------------------------------
def headline_kpis(fact: pd.DataFrame) -> dict:
    """Headline numbers for the rows supplied. Unit: user (orders/revenue: order).

    purchase_conversion = users with >=1 purchase / active users, same rows.
    """
    active_users = fact["user_pseudo_id"].nunique()
    purchasers = fact.loc[fact["purchased"] == 1, "user_pseudo_id"].nunique()
    orders = int(fact["transactions"].sum())
    revenue = float(fact["revenue_usd"].sum())
    return {
        "active_users": int(active_users),
        "sessions": int(fact["sessions"].sum()),
        "events": int(fact["events"].sum()),
        "purchasers": int(purchasers),
        "orders": orders,
        "revenue_usd": round(revenue, 2),
        "purchase_conversion": safe_div(purchasers, active_users),
        "average_order_value": safe_div(revenue, orders),
        "revenue_per_user": safe_div(revenue, active_users),
    }


def daily_trend(fact: pd.DataFrame) -> pd.DataFrame:
    """One row per day: active users, purchasers, conversion, orders, revenue."""
    g = fact.groupby("event_dt")
    out = pd.DataFrame({
        "active_users": g["user_pseudo_id"].nunique(),
        "purchasers": fact[fact["purchased"] == 1].groupby("event_dt")["user_pseudo_id"].nunique(),
        "orders": g["transactions"].sum(),
        "revenue_usd": g["revenue_usd"].sum(),
        "events": g["events"].sum(),
    }).fillna({"purchasers": 0})
    out["purchasers"] = out["purchasers"].astype(int)
    out["purchase_conversion"] = out["purchasers"] / out["active_users"]
    return out.reset_index()


# --------------------------------------------------------------------------
# Funnel (user-level, stage presence)
# --------------------------------------------------------------------------
def user_stage_flags(fact: pd.DataFrame) -> pd.DataFrame:
    """One row per user: 1 if the user fired the stage event on any supplied row."""
    return fact.groupby("user_pseudo_id")[STAGE_COLUMNS].max()


def user_funnel(fact: pd.DataFrame) -> pd.DataFrame:
    """User-level STAGE-PRESENCE funnel. Unit: user.

    Not sequential: it says how many users did each thing at least once,
    in any order, inside the rows supplied.
    """
    flags = user_stage_flags(fact)
    users = [int(flags[c].sum()) for c in STAGE_COLUMNS]
    df = pd.DataFrame({"stage": STAGE_LABELS, "users": users})
    df["pct_of_first_stage"] = df["users"] / df["users"].iloc[0] if users[0] else np.nan
    df["step_conversion"] = df["users"] / df["users"].shift(1)
    df["drop_off_users"] = df["users"].shift(1) - df["users"]
    df["drop_off_rate"] = 1 - df["step_conversion"]
    return df


def user_funnel_by(fact_dims: pd.DataFrame, column: str) -> pd.DataFrame:
    """Stage-presence funnel split by a user attribute (e.g. 'device_category')."""
    flags = user_stage_flags(fact_dims)
    attr = fact_dims.groupby("user_pseudo_id")[column].first()
    flags = flags.join(attr)
    out = flags.groupby(column).agg(
        users=("viewed_item", "size"),
        users_viewed=("viewed_item", "sum"),
        users_added_cart=("added_cart", "sum"),
        users_began_checkout=("began_checkout", "sum"),
        users_purchased=("purchased", "sum"),
    ).reset_index()
    out["view_to_cart_rate"] = out["users_added_cart"] / out["users_viewed"]
    out["cart_to_checkout_rate"] = out["users_began_checkout"] / out["users_added_cart"]
    out["checkout_to_purchase_rate"] = out["users_purchased"] / out["users_began_checkout"]
    out["view_to_purchase_rate"] = out["users_purchased"] / out["users_viewed"]
    out["user_purchase_conversion"] = out["users_purchased"] / out["users"]
    return out.sort_values("users", ascending=False).reset_index(drop=True)


def largest_drop_off(funnel: pd.DataFrame, users_column: str = "users") -> dict:
    """Which step loses the largest SHARE of the users (or sessions) who reached it?"""
    best = None
    for i in range(1, len(funnel)):
        prev, cur = funnel[users_column].iloc[i - 1], funnel[users_column].iloc[i]
        rate = 1 - safe_div(cur, prev)
        if best is None or (not math.isnan(rate) and rate > best["drop_off_rate"]):
            best = {
                "from_stage": funnel["stage"].iloc[i - 1],
                "to_stage": funnel["stage"].iloc[i],
                "from_count": int(prev),
                "to_count": int(cur),
                "drop_off_rate": rate,
            }
    return best


# --------------------------------------------------------------------------
# Funnel (sequential, session level) - from the session_funnel export
# --------------------------------------------------------------------------
def session_funnel_table(session_funnel: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """Aggregate the sequential session funnel export. Unit: session."""
    cols = ["sessions", "seq_view", "seq_cart", "seq_checkout", "seq_purchase", "any_purchase"]
    if by is None:
        out = session_funnel[cols].sum().to_frame().T
    else:
        out = session_funnel.groupby(by)[cols].sum().reset_index()
    out["view_to_cart_rate"] = out["seq_cart"] / out["seq_view"]
    out["cart_to_checkout_rate"] = out["seq_checkout"] / out["seq_cart"]
    out["checkout_to_purchase_rate"] = out["seq_purchase"] / out["seq_checkout"]
    out["view_to_purchase_rate"] = out["seq_purchase"] / out["seq_view"]
    return out.sort_values("sessions", ascending=False).reset_index(drop=True)


def session_funnel_long(session_funnel: pd.DataFrame) -> pd.DataFrame:
    """Sequential session funnel in the same stage/count shape as user_funnel()."""
    t = session_funnel[["seq_view", "seq_cart", "seq_checkout", "seq_purchase"]].sum()
    df = pd.DataFrame({"stage": STAGE_LABELS, "sessions": [int(v) for v in t.values]})
    df["step_conversion"] = df["sessions"] / df["sessions"].shift(1)
    df["drop_off_rate"] = 1 - df["step_conversion"]
    return df


# --------------------------------------------------------------------------
# Cohort retention
# --------------------------------------------------------------------------
def cohort_retention(fact: pd.DataFrame, dim: pd.DataFrame) -> pd.DataFrame:
    """Monthly ACTIVITY retention. Unit: user.

    cohort_month = month of the user's first observed event in the sample.
    A user is retained in month N if they have any event in that month.
    Months after the data ends simply have no row (blank, not zero).
    """
    df = fact[["user_pseudo_id", "event_dt"]].merge(
        dim[["user_pseudo_id", "cohort_month"]], on="user_pseudo_id", validate="many_to_one")
    activity_month = df["event_dt"].dt.to_period("M")
    cohort_period = df["cohort_month"].dt.to_period("M")
    df["month_number"] = (
        (activity_month.dt.year - cohort_period.dt.year) * 12
        + (activity_month.dt.month - cohort_period.dt.month)
    )
    out = (df.groupby(["cohort_month", "month_number"])["user_pseudo_id"]
             .nunique().rename("active_users").reset_index())
    sizes = out[out["month_number"] == 0].set_index("cohort_month")["active_users"]
    out["cohort_users"] = out["cohort_month"].map(sizes)
    out["retention_rate"] = out["active_users"] / out["cohort_users"]
    return out.sort_values(["cohort_month", "month_number"]).reset_index(drop=True)


def cohort_matrix(retention: pd.DataFrame, value: str = "retention_rate") -> pd.DataFrame:
    """Pivot the long cohort table into cohort rows x month-number columns."""
    m = retention.pivot(index="cohort_month", columns="month_number", values=value)
    m.index = [d.strftime("%Y-%m") for d in m.index]
    m.index.name = "cohort_month"
    return m


# --------------------------------------------------------------------------
# Engagement features and rule-based segments
# --------------------------------------------------------------------------
def engagement_features(fact: pd.DataFrame, dim: pd.DataFrame, analysis_date=None) -> pd.DataFrame:
    """One row per user with transparent activity features. Unit: user.

    analysis_date defaults to the last date in the data and must be stated
    whenever these features are reported.
    """
    analysis_date = pd.Timestamp(analysis_date) if analysis_date is not None else fact["event_dt"].max()
    recent_start = analysis_date - pd.Timedelta(days=29)        # last 30 days
    prior_start = recent_start - pd.Timedelta(days=30)          # the 30 days before that

    g = fact.groupby("user_pseudo_id")
    feats = pd.DataFrame({
        "active_days": g["event_dt"].nunique(),
        "sessions": g["sessions"].sum(),
        "events": g["events"].sum(),
        "engagement_min": g["engagement_sec"].sum() / 60,
        "viewed_item": g["viewed_item"].max(),
        "added_cart": g["added_cart"].max(),
        "purchased": g["purchased"].max(),
        "purchase_count": g["transactions"].sum(),
        "revenue_usd": g["revenue_usd"].sum(),
        "last_event_dt": g["event_dt"].max(),
    })
    recent = fact[fact["event_dt"] >= recent_start].groupby("user_pseudo_id")["event_dt"].nunique()
    prior = fact[(fact["event_dt"] >= prior_start) & (fact["event_dt"] < recent_start)] \
        .groupby("user_pseudo_id")["event_dt"].nunique()
    feats["active_days_30d"] = recent.reindex(feats.index).fillna(0).astype(int)
    feats["active_days_prior_30d"] = prior.reindex(feats.index).fillna(0).astype(int)
    feats["days_since_last_event"] = (analysis_date - feats["last_event_dt"]).dt.days

    feats = feats.join(dim.set_index("user_pseudo_id")[
        ["first_seen_dt", "cohort_month", "device_category", "country", "channel_group"]])
    feats["observed_days"] = (analysis_date - feats["first_seen_dt"]).dt.days + 1

    # Rule-based segment (same thresholds as sql/07_segment_analysis.sql Q34)
    high = (feats["active_days"] >= 3) | (feats["purchased"] == 1)
    medium = (feats["active_days"] == 2) | (feats["viewed_item"] == 1) | (feats["added_cart"] == 1)
    feats["engagement_segment"] = np.select([high, medium], ["1 High", "2 Medium"], default="3 Low")

    # Declining-activity indicator: active in the prior 30 days, silent in the last 30.
    # Only defined for users first seen before the prior window ended.
    eligible = feats["first_seen_dt"] < recent_start
    feats["declining_activity"] = np.where(
        eligible, (feats["active_days_prior_30d"] > 0) & (feats["active_days_30d"] == 0), np.nan)
    feats.attrs["analysis_date"] = analysis_date
    return feats.reset_index()


# --------------------------------------------------------------------------
# Statistics for the (simulated) A/B test
# --------------------------------------------------------------------------
def sample_size_two_proportions(p_baseline: float, mde_abs: float,
                                alpha: float = 0.05, power: float = 0.80) -> int:
    """Users needed PER GROUP for a two-sided test of two proportions."""
    p1, p2 = p_baseline, p_baseline + mde_abs
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    p_bar = (p1 + p2) / 2
    n = ((z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
          + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (mde_abs ** 2)
    return math.ceil(n)


def two_proportion_test(x_control: int, n_control: int, x_treat: int, n_treat: int,
                        alpha: float = 0.05) -> dict:
    """Two-sided z-test for a difference in proportions, with a confidence interval."""
    p_c, p_t = x_control / n_control, x_treat / n_treat
    diff = p_t - p_c
    p_pool = (x_control + x_treat) / (n_control + n_treat)
    se_pooled = math.sqrt(p_pool * (1 - p_pool) * (1 / n_control + 1 / n_treat))
    z = diff / se_pooled
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    se_unpooled = math.sqrt(p_c * (1 - p_c) / n_control + p_t * (1 - p_t) / n_treat)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    return {
        "control_rate": p_c,
        "treatment_rate": p_t,
        "absolute_lift": diff,
        "relative_lift": diff / p_c if p_c else float("nan"),
        "z": z,
        "p_value": p_value,
        "ci_low": diff - z_crit * se_unpooled,
        "ci_high": diff + z_crit * se_unpooled,
        "confidence_level": 1 - alpha,
    }


def sample_ratio_mismatch(n_control: int, n_treat: int, expected_share: float = 0.5) -> dict:
    """Chi-square check that the split matches the planned ratio (SRM)."""
    total = n_control + n_treat
    expected = [total * (1 - expected_share), total * expected_share]
    chi2, p = stats.chisquare([n_control, n_treat], f_exp=expected)
    return {"chi2": float(chi2), "p_value": float(p), "srm_detected": bool(p < 0.001)}


def wilson_interval(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson confidence interval for one proportion (safe for small rates)."""
    if n == 0:
        return float("nan"), float("nan")
    z = stats.norm.ppf(1 - alpha / 2)
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half
