-- =====================================================================
-- ProductPulse AI | 04_funnel_analysis.sql
-- Purpose : Measure view_item -> add_to_cart -> begin_checkout -> purchase.
-- Requires: the views from 00_create_views.sql.
--
-- TWO DIFFERENT FUNNELS ARE DEFINED HERE. Always say which one you mean.
--   A) User-level STAGE-PRESENCE funnel (Q19, Q20):
--      did the user fire each event at least once, at any time, in any
--      order, during the whole sample?
--   B) SEQUENTIAL SESSION funnel (Q21, Q22):
--      inside ONE session, did each stage happen at or after the stage
--      before it?
-- Funnel B is stricter, so its counts are lower.
-- =====================================================================


-- Q19. User-level stage-presence funnel (overall) -----------------------
-- Grain: one row for the whole sample. Unit = USER.
-- Denominator of every "view_to_*" rate: users who viewed an item.
WITH user_stage AS (
  SELECT
    user_pseudo_id,
    MAX(IF(event_name = 'view_item', 1, 0))       AS viewed_item,
    MAX(IF(event_name = 'add_to_cart', 1, 0))     AS added_cart,
    MAX(IF(event_name = 'begin_checkout', 1, 0))  AS began_checkout,
    MAX(IF(event_name = 'purchase', 1, 0))        AS purchased
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
)
SELECT
  COUNT(*)                                AS all_users,
  COUNTIF(viewed_item = 1)                AS users_viewed,
  COUNTIF(added_cart = 1)                 AS users_added_cart,
  COUNTIF(began_checkout = 1)             AS users_began_checkout,
  COUNTIF(purchased = 1)                  AS users_purchased,
  ROUND(SAFE_DIVIDE(COUNTIF(added_cart = 1),     COUNTIF(viewed_item = 1)), 4)     AS view_to_cart_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(began_checkout = 1), COUNTIF(added_cart = 1)), 4)      AS cart_to_checkout_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(purchased = 1),      COUNTIF(began_checkout = 1)), 4)  AS checkout_to_purchase_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(purchased = 1),      COUNTIF(viewed_item = 1)), 4)     AS view_to_purchase_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(purchased = 1),      COUNT(*)), 4)                     AS user_purchase_conversion,
  -- Because this is stage PRESENCE, a later stage can happen without an
  -- earlier one. These two columns show how often that occurs.
  COUNTIF(purchased = 1 AND viewed_item = 0)     AS purchasers_without_view_item,
  COUNTIF(added_cart = 1 AND viewed_item = 0)    AS cart_users_without_view_item
FROM user_stage;


-- Q20. User-level stage-presence funnel by first-observed device --------
-- Grain: one row per device category. Unit = USER.
-- Each user is assigned ONE device: the device of their first event
-- (ROW_NUMBER window function). Same rule as dim_user, so the numbers
-- reconcile with the dashboard.
WITH ranked AS (
  SELECT
    user_pseudo_id,
    device_category,
    ROW_NUMBER() OVER (
      PARTITION BY user_pseudo_id
      ORDER BY event_timestamp, event_name) AS rn
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
),
first_device AS (
  SELECT user_pseudo_id, device_category
  FROM ranked
  WHERE rn = 1
),
user_stage AS (
  SELECT
    user_pseudo_id,
    MAX(IF(event_name = 'view_item', 1, 0))       AS viewed_item,
    MAX(IF(event_name = 'add_to_cart', 1, 0))     AS added_cart,
    MAX(IF(event_name = 'begin_checkout', 1, 0))  AS began_checkout,
    MAX(IF(event_name = 'purchase', 1, 0))        AS purchased
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
)
SELECT
  d.device_category,
  COUNT(*)                          AS users,
  COUNTIF(s.viewed_item = 1)        AS users_viewed,
  COUNTIF(s.added_cart = 1)         AS users_added_cart,
  COUNTIF(s.began_checkout = 1)     AS users_began_checkout,
  COUNTIF(s.purchased = 1)          AS users_purchased,
  ROUND(SAFE_DIVIDE(COUNTIF(s.added_cart = 1), COUNTIF(s.viewed_item = 1)), 4) AS view_to_cart_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(s.purchased = 1),  COUNTIF(s.viewed_item = 1)), 4) AS view_to_purchase_rate
FROM user_stage AS s
JOIN first_device AS d USING (user_pseudo_id)     -- 1:1 join, cannot multiply rows
GROUP BY d.device_category
ORDER BY users DESC;

-- Validation for Q20: SUM(users) must equal all_users in Q19, and each
-- stage column must sum to the matching column in Q19.


-- Q21. Sequential session funnel (overall) ------------------------------
-- Grain: one row for the whole sample. Unit = SESSION.
-- A session reaches stage N only if stage N happened at or after the first
-- time it reached stage N-1, inside the same session.
-- Built with window functions: each CTE adds the timestamp of the next stage.
WITH ev AS (
  SELECT user_pseudo_id, ga_session_id, event_name, event_timestamp
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
    AND ga_session_id IS NOT NULL
),
s1 AS (
  SELECT *,
    MIN(IF(event_name = 'view_item', event_timestamp, NULL))
      OVER (PARTITION BY user_pseudo_id, ga_session_id) AS t_view
  FROM ev
),
s2 AS (
  SELECT *,
    MIN(IF(event_name = 'add_to_cart' AND event_timestamp >= t_view, event_timestamp, NULL))
      OVER (PARTITION BY user_pseudo_id, ga_session_id) AS t_cart
  FROM s1
),
s3 AS (
  SELECT *,
    MIN(IF(event_name = 'begin_checkout' AND event_timestamp >= t_cart, event_timestamp, NULL))
      OVER (PARTITION BY user_pseudo_id, ga_session_id) AS t_checkout
  FROM s2
),
s4 AS (
  SELECT *,
    MIN(IF(event_name = 'purchase' AND event_timestamp >= t_checkout, event_timestamp, NULL))
      OVER (PARTITION BY user_pseudo_id, ga_session_id) AS t_purchase
  FROM s3
),
per_session AS (
  SELECT
    user_pseudo_id,
    ga_session_id,
    MAX(t_view)      AS t_view,
    MAX(t_cart)      AS t_cart,
    MAX(t_checkout)  AS t_checkout,
    MAX(t_purchase)  AS t_purchase,
    MAX(IF(event_name = 'purchase', 1, 0)) AS any_purchase
  FROM s4
  GROUP BY user_pseudo_id, ga_session_id
)
SELECT
  COUNT(*)                            AS sessions,
  COUNTIF(t_view IS NOT NULL)         AS seq_view,
  COUNTIF(t_cart IS NOT NULL)         AS seq_cart,
  COUNTIF(t_checkout IS NOT NULL)     AS seq_checkout,
  COUNTIF(t_purchase IS NOT NULL)     AS seq_purchase,
  COUNTIF(any_purchase = 1)           AS sessions_with_any_purchase,
  ROUND(SAFE_DIVIDE(COUNTIF(t_cart IS NOT NULL),     COUNTIF(t_view IS NOT NULL)), 4)     AS view_to_cart_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(t_checkout IS NOT NULL), COUNTIF(t_cart IS NOT NULL)), 4)     AS cart_to_checkout_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(t_purchase IS NOT NULL), COUNTIF(t_checkout IS NOT NULL)), 4) AS checkout_to_purchase_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(t_purchase IS NOT NULL), COUNTIF(t_view IS NOT NULL)), 4)     AS view_to_purchase_rate
FROM per_session;
-- sessions_with_any_purchase - seq_purchase = purchases that did not follow
-- the full view -> cart -> checkout path inside one session (for example a
-- cart filled in an earlier session). That gap is itself a finding.


-- Q22. Time between funnel stages (sequential, same session) ------------
-- Grain: one row for the whole sample. Unit = SESSION that completed the step.
-- Median minutes from one stage to the next, for sessions that did both.
WITH ev AS (
  SELECT user_pseudo_id, ga_session_id, event_name, event_timestamp
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
    AND ga_session_id IS NOT NULL
    AND event_name IN ('view_item', 'add_to_cart', 'begin_checkout', 'purchase')
),
per_session AS (
  SELECT
    user_pseudo_id,
    ga_session_id,
    MIN(IF(event_name = 'view_item',      event_timestamp, NULL)) AS t_view,
    MIN(IF(event_name = 'add_to_cart',    event_timestamp, NULL)) AS t_cart,
    MIN(IF(event_name = 'begin_checkout', event_timestamp, NULL)) AS t_checkout,
    MAX(IF(event_name = 'purchase',       event_timestamp, NULL)) AS t_purchase
  FROM ev
  GROUP BY user_pseudo_id, ga_session_id
)
SELECT
  COUNTIF(t_cart >= t_view)                                               AS sessions_view_then_cart,
  ROUND(APPROX_QUANTILES(IF(t_cart >= t_view,
        (t_cart - t_view) / 60e6, NULL), 2)[OFFSET(1)], 2)                AS median_min_view_to_cart,
  COUNTIF(t_checkout >= t_cart)                                           AS sessions_cart_then_checkout,
  ROUND(APPROX_QUANTILES(IF(t_checkout >= t_cart,
        (t_checkout - t_cart) / 60e6, NULL), 2)[OFFSET(1)], 2)            AS median_min_cart_to_checkout,
  COUNTIF(t_purchase >= t_checkout)                                       AS sessions_checkout_then_purchase,
  ROUND(APPROX_QUANTILES(IF(t_purchase >= t_checkout,
        (t_purchase - t_checkout) / 60e6, NULL), 2)[OFFSET(1)], 2)        AS median_min_checkout_to_purchase
FROM per_session;
