# Executive summary

**Scope.** Google Merchandise Store, public obfuscated GA4 sample, 1 November 2020 to 31 January 2021. 4,295,584 events, 270,154 users (distinct `user_pseudo_id`), 360,129 sessions, 4,451 validated orders, $308,200 revenue (about $69 per order). Every number below comes from [`kpi_snapshot.md`](kpi_snapshot.md), generated on 2026-11-11 from the BigQuery export.

**One-line answer.** Most of the loss in the purchase path happens before the cart: four in five users who view a product never add one. Nine in ten users are seen on a single day, and device makes almost no difference to conversion.

## Three findings

**1. The largest drop-off is between viewing a product and adding it to the cart.**
79.52% of the 61,252 users who viewed an item (48,707 users) never added one to the cart; 20.48% did (12,545 users) (user-level funnel, Q19). A single visit shows the same picture: 19.69% of sessions with a product view went on to an add-to-cart (15,167 of 77,020 sessions, Q21). The next largest loss is at checkout: 54.51% of the 9,715 users who began checkout (5,296 users) did not purchase.

**2. Desktop and mobile users convert at almost the same rate.**
User purchase conversion was 1.60% on desktop (2,518 / 156,905 users) and 1.68% on mobile (1,802 / 107,175 users) (Q20). The funnel steps are equally close: view-to-cart 20.36% vs 20.72%, cart-to-checkout 77.05% (5,600 / 7,268) vs 77.85% (3,898 / 5,007). For cart-to-checkout the mobile minus desktop difference is +0.80 points, 95% interval -0.70 to +2.30, p = 0.30. The interval includes zero, so this data gives no evidence of a device gap. Tablet (6,074 users) is too small to compare reliably.

**3. Most users are seen once, and few return the following month.**
89.00% of users (240,441 / 270,154) were active on a single day (Q25). Month-1 activity retention was 5.86% for the November cohort (4,651 / 79,421) and 2.53% for December (2,517 / 99,664); by month 2 the November cohort was at 1.52% (1,204 / 79,421) (Q23). The November figure is likely flattered: "first observed in November" includes existing customers whose earlier visits fall outside the sample.

<!-- Optional: add the 30-day return rate from notebook 04, section 3 ("Returned within 30 days: __% (__ / __)"). -->

## Other observations worth knowing

- **Channels.** Among identifiable first-touch channels, Referral had the highest user purchase conversion at 1.86% (744 / 40,019); Organic search and Paid search were both 1.53%, Direct 1.58% (Q31). The "Data deleted" group shows 7.20% (209 / 2,901), which is an obfuscation artefact on a small base and should not be read as a channel result. 18.5% of users fall under "Other" or "Data deleted".
- **Products.** The five most-viewed products convert viewers to buyers at very different rates: Super G Unisex Joggers 1.50% (221 / 14,713) and Google Zip Hoodie F/C 1.57% (218 / 13,869), against Google Campus Bike Eco Tee Navy 0.36% (41 / 11,339) and YouTube Icon Tee Grey 0.46% (58 / 12,696) (Q27).
- **The two funnels disagree on cart-to-checkout.** At user level 77.44% of cart users also began checkout (9,715 / 12,545). Inside a single session, in order, only 35.71% did (5,416 / 15,167 sessions). The data does not say why; it is investigation 2 below.

## Three recommended investigations

These are hypotheses to test, not conclusions. The data shows where; it does not show why.

| # | Investigate | Because (evidence) | How | What would change the plan |
|---|---|---|---|---|
| 1 | Why viewers do not add to cart, starting with the high-traffic, low-conversion products | Finding 1; the product observation (0.36% to 1.57% among the top five) | Break view-to-cart down by product, category and price band (Q27 to Q29); review the pages of the lowest-converting high-traffic items | If the low rates sit in a few products, it is a catalogue, price or stock question rather than a site-wide one |
| 2 | Why cart-to-checkout is 77% per user but 36% per session | The funnel disagreement above | Count sessions with `begin_checkout` but no earlier `add_to_cart`; measure days between a user's first cart and first checkout; check whether both events fire consistently | If most checkouts start in a later session, the site has a return-to-buy pattern and a single-session funnel understates it. If events fire inconsistently, it is a tracking issue |
| 3 | What distinguishes the 11% of users who return | Finding 3 | Compare return rates by first-touch channel and by whether the first visit included a product view (notebook 04, section 4) | If returners differ mainly by channel, acquisition quality matters more than on-site retention features |

**Not recommended as a priority: a mobile-specific fix.** Finding 2 shows no measurable device gap in this sample.

**Proposed experiment.** A simplified checkout tested against the current one, with purchase conversion per user who begins checkout as the primary metric. The measured baseline is 45.49% (4,419 / 9,715 users). At that baseline, detecting a +3 point lift with 80% power needs about 4,344 users per group. The design and decision rule are in [`experiment_memo.md`](experiment_memo.md); the analysis shown there uses simulated data with an assumed 40% baseline.

## What this summary does not claim

- No causal effect. Every comparison is observational.
- No business impact. Nothing was changed in a live product.
- No generalisation beyond this store and these three months, which include the holiday season.
- Channel results are first-touch and partly obfuscated.
- Orders and revenue are conservative: 906 of the 5,692 purchase events had no usable transaction id and are excluded.
- Users are browser or device ids, so single-day and retention figures overstate how many people never came back.

Full list: [`limitations.md`](limitations.md). Metric definitions: [`../docs/metric_definitions.md`](../docs/metric_definitions.md). Wording produced with AI assistance must be logged in [`../ai/insight_validation.md`](../ai/insight_validation.md) before this summary is published.
