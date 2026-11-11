# Interview preparation

Answer structure for every question: **Question → Metric definition → Method → Result → Limitation → Recommendation.** State the unit of analysis, the denominator and the filters. Be ready to open the query or notebook behind the answer.

Blanks (`____`) are for your own measured numbers from `reports/kpi_snapshot.md`. An answer with your real number and its denominator is far stronger than a general one.

## The 60-second story

"I built ProductPulse AI to answer an ecommerce product team's questions about conversion and retention. I used the public GA4 event dataset: BigQuery SQL to define and calculate user, funnel and cohort metrics, Python to check data quality and reconcile the numbers independently, and Power BI for an interactive four-page report. I also built a Claude-assisted workflow that drafts summaries from verified aggregate metrics and separates observations from hypotheses, with every sentence traced to a query. The data is a historical, obfuscated three-month sample, so I document its limits and I do not claim any causal business impact."

## The 5-minute demo

| Time | Show | Say |
|---|---|---|
| 0:30 | README top | The business problem, the dataset and its period |
| 1:00 | `docs/architecture.png`, `docs/metric_definitions.md` | BigQuery is the source of truth; every KPI has a numerator and denominator |
| 1:30 | Power BI pages 2 and 3 | Filter by device, drill through, show the tooltip with the denominator, show blank cohort cells |
| 1:00 | One finding | The number, its base, the query, and one limitation |
| 1:00 | `ai/insight_validation.md` | A kept, an edited and a rejected AI sentence |
| 0:40 | `reports/executive_summary.md` | The recommendation and the experiment that would test it |

## Questions and answers

**1. Why this dataset, and what are its limitations?**
It is real event-level GA4 data with nested parameters and item arrays, so the SQL problems are the ones analysts meet in practice, and it is public, so anyone can reproduce my numbers. Limits: three months only (1 Nov 2020 to 31 Jan 2021, including the holiday season), obfuscated values such as `<Other>` and `(data deleted)`, a browser-level id rather than a person, and it is observational. `____%` of users have an obfuscated channel.

**2. What is the difference between event count, session count and distinct users?**
Three units. An event is one row. A session is a visit, identified by `user_pseudo_id` plus `ga_session_id`, because the session id alone is not unique across users. A user is a distinct `user_pseudo_id`. In my data: `____` events, `____` sessions, `____` users. Mixing them is the most common error: for example dividing purchase *events* by *users* and calling it a conversion rate.

**3. How did you define purchase conversion, and what is the denominator?**
Distinct users with at least one purchase event, divided by distinct active users in the same period and filters. It came to `__%` (`____` / `____`). It is a user-level rate over the whole period, so it rises with a longer period. A session conversion rate would use sessions in both places and is lower.

**4. User-level funnel versus sequential session funnel?**
The user-level funnel is stage presence: did the user fire each event at least once, in any order, at any time. It answers "how many users ever get this far". The sequential funnel requires each stage to happen at or after the previous one inside one session, built with window functions that carry the previous stage's timestamp forward. It answers "how does one visit progress" and gives lower numbers because people often buy in a later session. I report both and label them. In my data `____` purchasing sessions did not follow the full in-session path.

**5. How did you extract nested GA4 event parameters?**
`event_params` is an array of key/value structs where the value sits in one of four typed fields. I first listed keys and which type each uses (Q03), then extracted each one with a scalar sub-query: `(SELECT ep.value.int_value FROM UNNEST(event_params) ep WHERE ep.key = 'ga_session_id')`. That returns one value per event, so it cannot multiply rows.

**6. How did you prevent double counting when unnesting item arrays?**
Three things. The unnest is isolated in one view, `items_base`, whose grain is documented as event x item. User and order counts from it use `COUNT(DISTINCT ...)`. Headline revenue never comes from item rows: it comes from `purchase_revenue_in_usd`, de-duplicated by `transaction_id`. I also measured the fan-out (Q12): `____` item rows per purchase event on average.

**7. How did you define a cohort and calculate retention?**
A cohort is the month of a user's first observed event. A user is retained in month N if they have any event in that calendar month. The query finds each user's cohort month, their distinct activity months, the month difference with `DATE_DIFF`, then divides active users by the cohort size. November month-1 retention was `__%` (`____` / `____`). I recomputed it in pandas and the notebook asserts the two tables match.

**8. Why can a late cohort have incomplete D7 or D30 observation?**
The data ends on 31 January. Someone first seen on 20 January has 11 days in which to return, so their 30-day retention is not yet knowable. Counting them as "not returned" biases retention down. I show unobserved cells as blank, and for a fair comparison I use a fixed 30-day window restricted to users first seen on or before 1 January.

**9. What does a p-value tell you, and what does it not?**
It is the probability of seeing a difference at least this large if there were truly no difference. It is not the probability that the hypothesis is true, and it says nothing about the size or business value of the effect. That is why I report the confidence interval and the effect size next to it.

**10. Why is your A/B test simulated, and why is it not evidence of impact?**
The dataset has no randomized assignment, and comparing groups that were not randomized would confound the change with who the users are. I generated data with a fixed seed to show the method: sample size from baseline, MDE, alpha and power; a sample-ratio check; a two-proportion test with an interval; a guardrail. The effect was something I typed in. In that run the test was inconclusive (+1.59 points, 95% CI -0.51 to +3.69, p = 0.138) even though the simulated true effect was +3 points, which shows what 80% power means.

**11. How did you validate Power BI measures against SQL?**
With all slicers cleared, the cards must equal specific SQL results: active users to Q01, the four funnel counts to Q19, orders and revenue to Q11, each cohort cell to Q23. Then I select mobile and compare with the mobile row of Q20, to prove the filter context is right. The model is one row per user per day, so `DISTINCTCOUNT` stays correct under any slicer. The checks are recorded in `docs/qa_checklist.md`.

**12. How did you stop Claude from inventing explanations or numbers?**
By controlling the input and reviewing the output. It receives only a file of verified aggregates, each with its numerator, denominator, segment and caveat. The prompt forbids new values and causes, requires metric ids on every observation, and requires hypotheses to be labelled unproven. A script flags any number in the answer that is not in the input. Then I check every sentence against five rules and log keep, edit or reject. In my log `____` of `____` sentences were edited or rejected.

**13. What would you investigate next if mobile conversion were lower?**
First, which step: view-to-cart, cart-to-checkout or checkout-to-purchase. Then whether the gap holds within the same channel and for new versus returning users, because mobile and desktop audiences differ. Then page-level evidence: errors, form fields, load time. Only then a randomized test of a specific change. I would not conclude "mobile checkout is broken" from the gap alone.

**14. What would you change if the product manager challenged your metric definition?**
I would ask what decision the metric is for. If they care about visit efficiency, a session conversion rate is the better fit and I already have it. If they want orders rather than buyers, the numerator becomes validated orders. Definitions live in one document and one view, so a change is made once, the affected numbers are recalculated, and the old and new values are shown side by side with the reason.

## More questions to practise

- Why is `traffic_source` first-touch, and what does that do to a channel comparison?
- Why one row per user per day instead of a daily summary table?
- Why are repeated purchase events a problem, and how did you handle revenue?
- Why did you not build a churn model?
- Which chart would you remove if the page had to be simpler, and why?
- What is the first thing you would do with six more months of data?

## Resume entry (use after the real export and the Power BI build are complete)

**ProductPulse AI: AI-assisted Product Analytics and Customer Retention Intelligence Platform**
*Python, BigQuery SQL, Power BI, pandas, SciPy, Claude*

- Built an end-to-end product analytics workflow on the public GA4 ecommerce event dataset (`____` events, `____` users, Nov 2020 to Jan 2021) to examine user journeys, conversion, product engagement and repeat activity.
- Wrote 34 documented BigQuery SQL analyses using CTEs, conditional aggregation and window functions for user-level and sequential session funnels and monthly cohorts.
- Performed Python data-quality checks (27 automated checks), cohort analysis and statistical testing, reconciling Python results to SQL; designed and analysed a clearly labelled simulated A/B test.
- Designed a four-page interactive Power BI report with KPI cards, slicers, drill-through, tooltips and a cohort heatmap, with measures reconciled to SQL.
- Created a Claude-assisted insight workflow that summarises verified aggregate metrics, separates observations from hypotheses and logs human validation of every statement.

Add a measured result only with its scope, for example: "identified `________` as the largest funnel step drop-off (`__%` of `____` users, Nov 2020 to Jan 2021)".
