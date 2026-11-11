# Insight validation log

An AI draft is not a finding. A sentence becomes a finding only after a person has traced it to a query result and recorded that here.

## The five checks (run on every sentence)

| # | Check | Pass when |
|---|---|---|
| 1 | Number | The exact value appears in `reports/kpi_snapshot.md` (and therefore in a SQL result) |
| 2 | Period | The sentence refers to 2020-11-01 to 2021-01-31, or the stated sub-period matches the metric |
| 3 | Group and denominator | The comparison group and the base population match the metric's `segment` and `denominator` |
| 4 | Fact vs hypothesis | Anything about *why* is labelled "Hypothesis (unproven)" |
| 5 | Recommendation | It follows from the evidence, or is clearly framed as something to investigate |

Verdicts: **Keep** (all checks pass), **Edit** (true but needs rewording or a caveat), **Reject** (unsupported or wrong).

`find_unsupported_numbers()` in `productpulse/insights.py` does a first pass on check 1 automatically. It cannot do checks 2 to 5.

## Procedure

1. `python scripts/build_metric_summary.py` → refreshes `ai/verified_metrics.json` and `reports/kpi_snapshot.md`.
2. `python scripts/ask_claude.py` (or paste the printed prompt into claude.ai). The draft is saved in `ai/outputs/`.
3. Copy each sentence of the draft into the log table below and run the five checks.
4. Only **Keep** and corrected **Edit** rows may be copied into `reports/executive_summary.md`.
5. Commit the draft, this log and the final summary together so the trail is visible.

## Validation log: real data

Fill this in after your BigQuery export. One row per sentence.

Run date: ____  Metrics file: `ai/verified_metrics.json` generated on ____  Model: ____

| # | AI statement (verbatim) | Metric id(s) | Value in snapshot | Period ok | Denominator ok | Type | Verdict | Edit made / reason |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | Fact / Hypothesis / Recommendation | Keep / Edit / Reject | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |
| 6 | | | | | | | | |
| 7 | | | | | | | | |
| 8 | | | | | | | | |

Summary: ____ statements checked, ____ kept, ____ edited, ____ rejected.

---

## Worked example on SYNTHETIC DEMO DATA

> Everything in this section uses `ai/verified_metrics.DEMO.json`, built from the invented data in `data/demo/`. The numbers are **not findings** about the Google Merchandise Store. The example exists to show what a review looks like, including the kinds of errors to catch. The "draft" was written for this example and deliberately contains mistakes.

**Input (extract of the supplied metrics)**

| Metric id | Value | Numerator | Denominator |
|---|---|---|---|
| `funnel_user_view_to_cart` | 25.18% | 1,135 users with 'Add to cart' | 4,508 users with 'View item' |
| `funnel_user_largest_drop_off` | 74.82% | 3,373 users not reaching 'Add to cart' | 4,508 users with 'View item' |
| `device_desktop_cart_to_checkout` | 51.44% | 358 users who began checkout | 696 users who added to cart |
| `device_mobile_cart_to_checkout` | 42.21% | 176 users who began checkout | 417 users who added to cart |
| `retention_2020-11_month_1` | 11.22% | 440 cohort users active in that month | 3,923 users in cohort |
| `retention_2020-12_month_1` | 10.80% | 434 cohort users active in that month | 4,017 users in cohort |

**Review of a draft answer**

| # | Draft statement | Metric id(s) | Check result | Verdict | Edit made / reason |
|---|---|---|---|---|---|
| 1 | "The largest step drop-off is from View item to Add to cart: 74.82% of the 4,508 users who viewed an item did not add one to the cart." | `funnel_user_largest_drop_off` | Number, period, denominator all match | **Keep** | None |
| 2 | "Among users who added to cart, 51.44% of desktop users (358 / 696) began checkout, compared with 42.21% of mobile users (176 / 417)." | `device_desktop_cart_to_checkout`, `device_mobile_cart_to_checkout` | Both values and bases match | **Keep** | None |
| 3 | "Mobile users abandon carts because the mobile checkout form is harder to use." | none | States a cause as fact. No metric describes the form or usability | **Edit** | Rewritten: "Hypothesis (unproven): the mobile checkout flow may be harder to complete. Usability data would be needed to test this." |
| 4 | "Month-1 retention fell from 11.22% for the November cohort to 10.80% for December, showing that retention is declining." | `retention_2020-11_month_1`, `retention_2020-12_month_1` | Numbers match, but "declining" is a trend claim from two cohorts 0.42 points apart | **Edit** | Rewritten: "Month-1 activity retention was 11.22% (440 / 3,923) for the November cohort and 10.80% (434 / 4,017) for December. Two cohorts are too few to call a trend." |
| 5 | "Overall, about 30% of visitors return within a month." | none | 30% appears in no supplied metric. Flagged by `find_unsupported_numbers()` | **Reject** | Invented figure |
| 6 | "Fixing the mobile checkout would raise revenue by roughly 9%." | none | Business impact that no metric supports; observational data cannot give it | **Reject** | Impact needs a randomized experiment |
| 7 | "Recommended: compare cart-to-checkout by device within each channel to see whether the gap holds." | device and channel metrics | A follow-up analysis that follows from statement 2 | **Keep** | None |

Summary of the example: 7 statements checked, 3 kept, 2 edited, 2 rejected.

**What the example teaches**

- The dangerous statements (3, 4, 6) sound the most useful. Being readable is not the same as being supported.
- Statement 4 has correct numbers and a wrong conclusion. Checking numbers alone is not enough.
- A rejected statement is a normal outcome of the workflow, not a failure of it.
