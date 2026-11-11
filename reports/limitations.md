# Limitations

What this analysis cannot tell you, and why. Read this before quoting any number from the project.

## The dataset

| Limitation | Consequence |
|---|---|
| **Historical.** 1 November 2020 to 31 January 2021 | Results describe that period only. It includes Black Friday, Cyber Monday and the December holidays, which are not typical months for a retailer |
| **Obfuscated.** Some values are replaced by `<Other>`, `(data deleted)` or `(not set)`, and some fields are removed or altered | Channel and geography comparisons are incomplete. Totals are not the store's real business figures |
| **Three months only** | At most two follow-up months, and only for the November cohort. No year-over-year comparison, no seasonality adjustment |
| **A sample, not a live production feed** | It cannot be refreshed and cannot be checked against a source system |
| **One store** | The Google Merchandise Store is a small branded-merchandise shop. Its patterns need not hold elsewhere |

## Identity

- `user_pseudo_id` identifies a browser or device, not a person. One person on a phone and a laptop is two "users". Clearing cookies creates a new one.
- Effect: distinct users are overstated, and retention and repeat purchase are **understated**.
- Each user is assigned the device and country of their first observed event. Users seen on several devices are counted once, under the first.

## Attribution

- `traffic_source` is the source that first acquired the user. Every later session carries the same value.
- A user acquired by organic search who returns from an email and buys is counted under organic search.
- Channel comparisons are therefore first-touch only and say nothing about which channel drove a given session or purchase.

## Funnel

- The user-level funnel is stage presence: each event at least once, in any order, across the whole period. It does not prove a sequence.
- The sequential session funnel requires order within one session, so it misses purchases that complete a cart from an earlier visit.
- Neither funnel says why users left a step.
- Funnel events depend on the site's tracking. A missing or duplicated tag would look like user behaviour.

## Retention and engagement

- Cohorts use first *observed* activity. A November "new" user may be a long-standing customer.
- Late cohorts have short follow-up. January users have had 0 to 30 days to return. Unobserved periods are shown blank, not as zero.
- Retention means any event, not a purchase and not satisfaction.
- "Inactive in the observed window" is not churn. Many such users may return after the sample ends.
- Engagement segments use thresholds chosen by the analyst. Different thresholds give different segment sizes.
- No predictive model is included, because the data has no defensible future-outcome label.

## Revenue

- Revenue is `purchase_revenue_in_usd`, counted once per valid `transaction_id`. Purchases without a usable id are excluded.
- Refunds, taxes, shipping and margins are not analysed.
- Item-level revenue is approximate where an order has repeated purchase events.

## Causality

- All data is observational. A difference between desktop and mobile, or between channels, may reflect who uses them rather than anything about the experience.
- Statistical tests in notebook 03 say whether a gap is larger than chance, not what caused it.
- The A/B test in notebook 05 and `experiment_memo.md` is **simulated**. It demonstrates a method. It is not evidence about any real change.

## The AI-assisted summary

- Claude sees only the aggregate metrics supplied to it and can still phrase a correct number misleadingly.
- The automatic number check catches invented figures, not invented reasoning.
- A sentence is treated as a finding only after the human review recorded in `ai/insight_validation.md`.

## What this project does not claim

It does not claim to have improved conversion, retention or revenue for any company. It analyses a public sample and recommends what to investigate. Demonstrating impact would require a randomized experiment on a live product.
