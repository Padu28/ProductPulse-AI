-- =====================================================================
-- ProductPulse AI | 07_segment_analysis.sql
-- Purpose : Compare acquisition channels, countries and engagement levels.
-- Requires: the views from 00_create_views.sql.
--
-- Attribution caveat: traffic_source in the GA4 export is the source that
-- FIRST acquired the user. It is not the source of each session, so these
-- are first-touch comparisons only. '<Other>' and '(data deleted)' are
-- obfuscation artefacts of the public sample and are shown, not hidden.
-- =====================================================================


-- Q31. Users, purchasers, orders and revenue by acquisition channel ------
-- Grain: one row per channel_group. Unit = USER (orders/revenue per order).
WITH users AS (
  SELECT
    user_pseudo_id,
    MIN(channel_group)                              AS channel_group,   -- constant per user
    MAX(IF(event_name = 'view_item', 1, 0))         AS viewed_item,
    MAX(IF(event_name = 'purchase', 1, 0))          AS purchased
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
),
tx AS (
  SELECT
    transaction_id,
    MIN(user_pseudo_id)        AS user_pseudo_id,
    MAX(purchase_revenue_usd)  AS revenue_usd
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE event_name = 'purchase'
    AND user_pseudo_id IS NOT NULL
    AND transaction_id IS NOT NULL
    AND transaction_id != '(not set)'
  GROUP BY transaction_id
),
user_tx AS (
  SELECT user_pseudo_id, COUNT(*) AS orders, SUM(revenue_usd) AS revenue_usd
  FROM tx
  GROUP BY user_pseudo_id
)
SELECT
  u.channel_group,
  COUNT(*)                                                   AS users,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)           AS pct_of_users,
  COUNTIF(u.viewed_item = 1)                                 AS users_viewed_item,
  COUNTIF(u.purchased = 1)                                   AS purchasers,
  ROUND(SAFE_DIVIDE(COUNTIF(u.purchased = 1), COUNT(*)), 4)  AS user_purchase_conversion,
  IFNULL(SUM(t.orders), 0)                                   AS orders,
  ROUND(IFNULL(SUM(t.revenue_usd), 0), 2)                    AS revenue_usd,
  ROUND(SAFE_DIVIDE(SUM(t.revenue_usd), COUNT(*)), 2)        AS revenue_per_user,
  ROUND(SAFE_DIVIDE(SUM(t.revenue_usd), SUM(t.orders)), 2)   AS average_order_value
FROM users AS u
LEFT JOIN user_tx AS t USING (user_pseudo_id)    -- user_tx is 1 row per user: no fan-out
GROUP BY u.channel_group
ORDER BY users DESC;


-- Q32. Top countries by users, with conversion ---------------------------
-- Grain: one row per country (first-observed country per user). Unit = USER.
WITH ranked AS (
  SELECT
    user_pseudo_id,
    country,
    ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY event_timestamp, event_name) AS rn
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
),
first_country AS (
  SELECT user_pseudo_id, country FROM ranked WHERE rn = 1
),
buyers AS (
  SELECT DISTINCT user_pseudo_id
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE event_name = 'purchase' AND user_pseudo_id IS NOT NULL
)
SELECT
  IFNULL(NULLIF(c.country, ''), '(not set)')                         AS country,
  COUNT(*)                                                           AS users,
  COUNT(b.user_pseudo_id)                                            AS purchasers,
  ROUND(SAFE_DIVIDE(COUNT(b.user_pseudo_id), COUNT(*)), 4)           AS user_purchase_conversion
FROM first_country AS c
LEFT JOIN buyers AS b USING (user_pseudo_id)
GROUP BY 1
HAVING COUNT(*) >= 1000          -- small countries give unstable rates
ORDER BY users DESC
LIMIT 20;


-- Q33. Sequential session funnel by device and channel -------------------
-- Grain: one row per device_category x channel_group. Unit = SESSION.
-- Same logic as Q21, split by segment. Counts are additive across rows
-- because every session belongs to exactly one row.
WITH ev AS (
  SELECT user_pseudo_id, ga_session_id, event_name, event_timestamp,
         device_category, channel_group
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
    AND ga_session_id IS NOT NULL
),
s1 AS (
  SELECT *, MIN(IF(event_name = 'view_item', event_timestamp, NULL))
              OVER (PARTITION BY user_pseudo_id, ga_session_id) AS t_view
  FROM ev
),
s2 AS (
  SELECT *, MIN(IF(event_name = 'add_to_cart' AND event_timestamp >= t_view, event_timestamp, NULL))
              OVER (PARTITION BY user_pseudo_id, ga_session_id) AS t_cart
  FROM s1
),
s3 AS (
  SELECT *, MIN(IF(event_name = 'begin_checkout' AND event_timestamp >= t_cart, event_timestamp, NULL))
              OVER (PARTITION BY user_pseudo_id, ga_session_id) AS t_checkout
  FROM s2
),
s4 AS (
  SELECT *, MIN(IF(event_name = 'purchase' AND event_timestamp >= t_checkout, event_timestamp, NULL))
              OVER (PARTITION BY user_pseudo_id, ga_session_id) AS t_purchase
  FROM s3
),
per_session AS (
  SELECT
    user_pseudo_id,
    ga_session_id,
    MIN(device_category)  AS device_category,
    MIN(channel_group)    AS channel_group,
    MAX(t_view)           AS t_view,
    MAX(t_cart)           AS t_cart,
    MAX(t_checkout)       AS t_checkout,
    MAX(t_purchase)       AS t_purchase,
    MAX(IF(event_name = 'purchase', 1, 0)) AS any_purchase
  FROM s4
  GROUP BY user_pseudo_id, ga_session_id
)
SELECT
  device_category,
  channel_group,
  COUNT(*)                         AS sessions,
  COUNTIF(t_view IS NOT NULL)      AS seq_view,
  COUNTIF(t_cart IS NOT NULL)      AS seq_cart,
  COUNTIF(t_checkout IS NOT NULL)  AS seq_checkout,
  COUNTIF(t_purchase IS NOT NULL)  AS seq_purchase,
  COUNTIF(any_purchase = 1)        AS any_purchase
FROM per_session
GROUP BY device_category, channel_group
ORDER BY sessions DESC;


-- Q34. Rule-based engagement segments -------------------------------------
-- Grain: one row per engagement_segment. Unit = USER.
-- Analysis date = 2021-01-31 (last day of the sample).
-- Thresholds are analytical choices, documented in docs/metric_definitions.md:
--   High   : active on 3+ days, or purchased
--   Medium : active on 2 days, or viewed an item / added to cart
--   Low    : everyone else (single day, no product interaction)
-- "Inactive 30+ days" means inactive IN THE OBSERVED WINDOW. It is not churn.
WITH per_user AS (
  SELECT
    user_pseudo_id,
    COUNT(DISTINCT event_dt)                          AS active_days,
    DATE_DIFF(DATE '2021-01-31', MAX(event_dt), DAY)  AS days_since_last_event,
    MAX(IF(event_name IN ('view_item', 'add_to_cart'), 1, 0)) AS product_interaction,
    MAX(IF(event_name = 'purchase', 1, 0))            AS purchased
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
),
segmented AS (
  SELECT
    *,
    CASE
      WHEN active_days >= 3 OR purchased = 1            THEN '1 High'
      WHEN active_days = 2 OR product_interaction = 1   THEN '2 Medium'
      ELSE '3 Low'
    END AS engagement_segment
  FROM per_user
)
SELECT
  engagement_segment,
  COUNT(*)                                            AS users,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)    AS pct_of_users,
  ROUND(AVG(active_days), 2)                          AS avg_active_days,
  ROUND(AVG(days_since_last_event), 1)                AS avg_days_since_last_event,
  COUNTIF(days_since_last_event >= 30)                AS inactive_30d_plus_in_window,
  COUNTIF(purchased = 1)                              AS purchasers
FROM segmented
GROUP BY engagement_segment
ORDER BY engagement_segment;
