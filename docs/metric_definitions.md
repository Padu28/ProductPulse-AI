# Metric definitions

One entry per KPI. If a number appears in a notebook, the dashboard or a report, its definition is here.

Rules that apply to every metric unless stated otherwise:

- **Period**: 2020-11-01 to 2021-01-31, or the dates selected in the report.
- **Null handling**: rows with a NULL `user_pseudo_id` are excluded.
- **Filters**: date, device (first observed), country (first observed), channel (first touch). Numerator and denominator always share the same filters.
- **Source**: the obfuscated public GA4 sample. Values are not the store's real business figures.

## Units of analysis

| Unit | How it is identified | Typical mistake |
|---|---|---|
| Event | One row in `events_*` | Treating event counts as people |
| Session | `user_pseudo_id` + `ga_session_id` | Counting `session_start` events, or using `ga_session_id` alone |
| User | DISTINCT `user_pseudo_id` | Adding daily or monthly users together |
| Item | One element of the `items` array | Summing users or revenue after `UNNEST` without re-aggregating |
| Order | DISTINCT valid `transaction_id` | Counting `purchase` events |

## Headline metrics

### Active users
| | |
|---|---|
| Business meaning | How many distinct visitors were seen |
| Formula | `COUNT(DISTINCT user_pseudo_id)` |
| Grain | User x selected period |
| SQL | `03_event_metrics.sql` Q14, Q15 |
| DAX | `[Active Users]` |
| Limitations | An id is a browser or device, not a person. Not additive across days, months or segments that share users |

### Sessions
| | |
|---|---|
| Business meaning | Number of visits |
| Formula | `COUNT(DISTINCT CONCAT(user_pseudo_id, '-', ga_session_id))` |
| Grain | Session x selected period |
| SQL | `03_event_metrics.sql` Q14, Q17; view `sessions_base` |
| Limitations | Events with a NULL session id are excluded. In `fact_user_day` a session crossing midnight is counted on both days |

### Validated orders
| | |
|---|---|
| Business meaning | Number of completed purchases |
| Formula | `COUNT(DISTINCT transaction_id)` where the id is not NULL and not `(not set)` |
| Grain | Order |
| SQL | `02_data_quality.sql` Q11; `03_event_metrics.sql` Q14 |
| DAX | `[Validated Orders]` |
| Limitations | Purchase events without a usable id are excluded, so the count is conservative |

### Revenue (USD)
| | |
|---|---|
| Business meaning | Value of validated orders |
| Formula | Per order `MAX(ecommerce.purchase_revenue_in_usd)`, then SUM over orders |
| Grain | Order, assigned to the day and user of its first purchase event |
| SQL | `02_data_quality.sql` Q11; `03_event_metrics.sql` Q14 |
| DAX | `[Revenue USD]` |
| Limitations | Obfuscated sample. NULL revenue is treated as 0. Refunds are not modelled |

### User purchase conversion rate
| | |
|---|---|
| Business meaning | Share of active users who bought at least once |
| Numerator | Distinct users with at least one `purchase` event |
| Denominator | Distinct active users, same period and filters |
| Grain | User x selected period |
| SQL | `04_funnel_analysis.sql` Q19 (`user_purchase_conversion`) |
| DAX | `[User Purchase Conversion]` |
| Limitations | Depends on the length of the period (longer period, more chances to buy). Uses purchase events, so it includes the few purchases without a valid transaction id. Not a session conversion rate |

### Average order value
| | |
|---|---|
| Numerator / denominator | Revenue (USD) / validated orders |
| DAX | `[Average Order Value]` |
| Limitations | Skewed by a few large orders; report the median from notebook 02 beside it |

## Funnel metrics

### User-level stage-presence funnel
| | |
|---|---|
| Business meaning | How many users ever get as far as each stage |
| Stages | `view_item`, `add_to_cart`, `begin_checkout`, `purchase` |
| Rule | A user counts for a stage if they fired the event at least once in the period, in any order, in any session |
| Step conversion | Users at stage N / users at stage N-1 |
| Share of first stage | Users at stage N / users who viewed an item |
| Drop-off rate | 1 - step conversion |
| Grain | User x selected period |
| SQL | `04_funnel_analysis.sql` Q19 (overall), Q20 (by device) |
| DAX | `[Funnel Users]`, `[Funnel Step Conversion]`, `[View to Cart Rate]` and related |
| Limitations | Not sequential. A user can be counted at a later stage without an earlier one (Q19 reports how many). Does not prove the stages happened in order |

### Sequential session funnel
| | |
|---|---|
| Business meaning | How a single visit progresses |
| Rule | Inside one session, stage N counts only if it happened at or after the first time the session reached stage N-1 |
| Time window | The session |
| Grain | Session, whole sample |
| SQL | `04_funnel_analysis.sql` Q21; `07_segment_analysis.sql` Q33 (by device and channel) |
| DAX | `[Seq View to Cart Rate]` and related (table `session_funnel`) |
| Limitations | A purchase that completes a cart from an earlier session is not counted in the sequence. `any_purchase` minus `seq_purchase` measures that gap. Not filterable by date in the dashboard |

### Viewer-to-buyer rate (product)
| | |
|---|---|
| Numerator | Distinct users who purchased the item |
| Denominator | Distinct users who viewed the item |
| Grain | Item, whole sample |
| SQL | `06_product_analysis.sql` Q27 |
| Limitations | An association. The view need not come before the purchase, and a buyer may never have fired `view_item` for it. Only valid for one item at a time |

## Retention metrics

### Monthly activity retention
| | |
|---|---|
| Business meaning | Do users come back in later months? |
| Cohort | Month of the user's first *observed* event |
| Numerator | Cohort users with any event in calendar month N after the cohort month |
| Denominator | All users in the cohort (month 0 = 100%) |
| Grain | Cohort month x month number |
| SQL | `05_cohort_retention.sql` Q23 |
| DAX | `[Retention Rate]`, `[Cohort Users]` |
| Limitations | First observed is not first ever. Only three months: November has two follow-up months, December one, January none. Unobserved cells are blank, never 0. Activity, not purchase |

### 30-day return rate
| | |
|---|---|
| Business meaning | Retention measured over the same window for everyone |
| Eligible users | First seen on or before 2021-01-01 (30 full days of follow-up) |
| Numerator | Eligible users active on any of days 1 to 30 after their first day |
| Denominator | Eligible users |
| Source | Notebook 04, section 3 |
| Limitations | Excludes users first seen in the last 30 days. Cookie loss looks like non-return |

### Single-day users
| | |
|---|---|
| Formula | Users with exactly one active date / all users |
| SQL | `05_cohort_retention.sql` Q25 |
| Limitations | Late arrivals have had less time to return |

### Repeat purchase rate
| | |
|---|---|
| Formula | Users with 2 or more validated orders / users with at least 1 |
| SQL | `05_cohort_retention.sql` Q26 |

## Engagement segments

Analysis date: 2021-01-31. The thresholds are analytical choices, not ground truth.

| Segment | Rule (first match wins) |
|---|---|
| 1 High | Active on 3 or more days, or purchased |
| 2 Medium | Active on exactly 2 days, or viewed an item, or added to cart |
| 3 Low | Everyone else |

| Indicator | Definition | Wording to use |
|---|---|---|
| Inactive 30+ days | `days_since_last_event >= 30`, reported for users first seen more than 30 days before the analysis date | "Inactive in the observed window". Never "churned" |
| Declining activity | Active in the 30 days before the last 30, and silent in the last 30 | "Declining activity indicator" |

SQL: `07_segment_analysis.sql` Q34. Python: `productpulse.metrics.engagement_features`.

## Template for a new metric

| Field | Fill in |
|---|---|
| Metric name | |
| Business meaning | |
| Numerator | |
| Denominator | |
| Grain | |
| Date window | |
| Filters | |
| Null handling | |
| SQL reference | |
| Known limitations | |
