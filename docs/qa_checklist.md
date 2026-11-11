# QA and acceptance checklist

Tick each line only after you have seen the evidence yourself. Write the evidence (a number, a query id, a date) in the last column.

## Acceptance tests

| # | Test | Pass condition | How to check | Done | Evidence |
|---|---|---|---|---|---|
| 1 | Date coverage | Queries use only 2020-11-01 to 2021-01-31; late-period limits documented | Q01; `reports/limitations.md` | ☐ | |
| 2 | User identity | NULL user ids handled explicitly; distinct-user denominators consistent | Q07; notebook 02 section 1 | ☐ | |
| 3 | Event parameter extraction | Correct key and value type; no accidental row multiplication | Q03, Q04; `COUNT(*)` of `events_base` equals Q01 | ☐ | |
| 4 | Item arrays | UNNEST isolated to item-level analysis or re-aggregated | Q12; only `items_base` and 06 use it | ☐ | |
| 5 | Funnel definition | Unit, sequence, time window and denominator documented | `docs/metric_definitions.md`; header of `04_funnel_analysis.sql` | ☐ | |
| 6 | Retention | Cohort definition and incomplete windows visible | Heatmap shows "not observed"; notebook 04 | ☐ | |
| 7 | Revenue | Currency and source field verified; duplication checked | Q11; notebook 02 section 5 | ☐ | |
| 8 | Python vs SQL | Funnel and cohort tables identical | "PASS" lines in notebooks 03 and 04 | ☐ | |
| 9 | Power BI vs SQL | Headline measures reconcile under the same filter | Table below | ☐ | |
| 10 | Interactions | Slicers, drill-through, tooltips, bookmarks and reset tested | Table below | ☐ | |
| 11 | AI output | Every number traces to a metric; hypotheses labelled; unsupported claims removed | `ai/insight_validation.md` log filled in | ☐ | |
| 12 | Reproducibility | README explains data access, queries and refresh | Follow README section 10 in a fresh folder | ☐ | |
| 13 | Privacy and security | No secrets or user-level data committed | `git status`; search the repo for `sk-ant`, `private_key` | ☐ | |

## Power BI reconciliation

All slicers cleared:

| Measure | Power BI | SQL / `kpi_snapshot.md` | Match |
|---|---|---|---|
| Active Users | | Q01 `identified_users`: | ☐ |
| Users Viewed Item | | Q19 `users_viewed`: | ☐ |
| Users Added to Cart | | Q19 `users_added_cart`: | ☐ |
| Users Began Checkout | | Q19 `users_began_checkout`: | ☐ |
| Purchasers | | Q19 `users_purchased`: | ☐ |
| Validated Orders | | Q11 `validated_orders`: | ☐ |
| Revenue USD | | Q11 `revenue_deduplicated`: | ☐ |
| Retention Rate, Nov cohort, month 1 | | Q23: | ☐ |

Device = mobile selected:

| Measure | Power BI | SQL Q20, mobile row | Match |
|---|---|---|---|
| Active Users | | | ☐ |
| Users Viewed Item | | | ☐ |
| Purchasers | | | ☐ |

## Interaction tests

| Test | Expected | Done |
|---|---|---|
| Pick a two-week date range | All visuals on pages 1 and 2 update; cohort heatmap does not (by design) | ☐ |
| Select Device = mobile | KPI cards, funnel and channel visuals all show mobile only | ☐ |
| Click a bar in "users by device" | Other visuals on the page filter, not just highlight | ☐ |
| Right-click a channel > Drill through | Segment detail page opens with that channel in context; Back returns | ☐ |
| Hover a conversion value | Tooltip page shows numerator, denominator and definition | ☐ |
| Press Reset | All slicers clear; Default view bookmark restored | ☐ |
| Navigation buttons | Each opens the right page; active page is highlighted | ☐ |
| Keyboard tab order and alt text | Logical order; every visual has alt text | ☐ |

## GitHub release checklist

- ☐ README renders, screenshots show, no broken links
- ☐ SQL files state the `YOUR_PROJECT` substitution
- ☐ Notebooks run top to bottom on the real export
- ☐ `powerbi/ProductPulse.pbix` and four screenshots present (or the access constraint explained)
- ☐ `reports/executive_summary.md` has three real findings and three investigations
- ☐ No `data/exports/`, `.venv/`, `.env`, keys or service-account files in the repository
- ☐ No number from `data/demo/` or the simulated A/B test presented as a finding
