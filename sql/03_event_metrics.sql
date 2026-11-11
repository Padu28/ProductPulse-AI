-- =====================================================================
-- ProductPulse AI | 03_event_metrics.sql
-- Purpose : Headline activity metrics: events, users, sessions, orders.
-- Requires: the views from 00_create_views.sql.
-- Reminder: events, sessions and users are three DIFFERENT units.
-- =====================================================================


-- Q14. Daily events, users, sessions, purchasers, orders and revenue ----
-- Grain: one row per calendar day (event_dt).
-- Orders and revenue are de-duplicated by transaction_id (see Q11).
-- An order is assigned to the day of its first purchase event.
WITH daily AS (
  SELECT
    event_dt,
    COUNT(*)                                                   AS total_events,
    COUNT(DISTINCT user_pseudo_id)                             AS active_users,
    COUNT(DISTINCT IF(ga_session_id IS NOT NULL,
          CONCAT(user_pseudo_id, '-', CAST(ga_session_id AS STRING)), NULL)) AS sessions,
    COUNT(DISTINCT IF(event_name = 'purchase', user_pseudo_id, NULL))        AS purchasers
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY event_dt
),
tx AS (
  SELECT
    transaction_id,
    MIN(event_dt)              AS purchase_dt,
    MAX(purchase_revenue_usd)  AS revenue_usd
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE event_name = 'purchase'
    AND user_pseudo_id IS NOT NULL
    AND transaction_id IS NOT NULL
    AND transaction_id != '(not set)'
  GROUP BY transaction_id
),
daily_tx AS (
  SELECT purchase_dt, COUNT(*) AS transactions, SUM(revenue_usd) AS revenue_usd
  FROM tx
  GROUP BY purchase_dt
)
SELECT
  d.event_dt,
  d.total_events,
  d.active_users,
  d.sessions,
  d.purchasers,
  IFNULL(t.transactions, 0)            AS transactions,
  ROUND(IFNULL(t.revenue_usd, 0), 2)   AS revenue_usd
FROM daily AS d
LEFT JOIN daily_tx AS t ON t.purchase_dt = d.event_dt
ORDER BY d.event_dt;

-- Validation for Q14: SUM(total_events) must equal the event_rows from Q01
-- minus null_user_id_rows from Q07.
-- SELECT COUNT(*) FROM `YOUR_PROJECT.productpulse.events_base` WHERE user_pseudo_id IS NOT NULL;


-- Q15. Monthly summary with purchase conversion -------------------------
-- Grain: one row per calendar month.
-- purchase_conversion = users with >=1 purchase event in the month
--                       / users active in the month.
SELECT
  DATE_TRUNC(event_dt, MONTH)                                        AS activity_month,
  COUNT(*)                                                           AS total_events,
  COUNT(DISTINCT user_pseudo_id)                                     AS active_users,
  COUNT(DISTINCT IF(event_name = 'purchase', user_pseudo_id, NULL))  AS purchasers,
  ROUND(SAFE_DIVIDE(
    COUNT(DISTINCT IF(event_name = 'purchase', user_pseudo_id, NULL)),
    COUNT(DISTINCT user_pseudo_id)), 4)                              AS purchase_conversion,
  ROUND(SAFE_DIVIDE(COUNT(*), COUNT(DISTINCT user_pseudo_id)), 2)    AS events_per_user
FROM `YOUR_PROJECT.productpulse.events_base`
WHERE user_pseudo_id IS NOT NULL
GROUP BY activity_month
ORDER BY activity_month;
-- Caution: monthly active users do NOT add up to total users (a user active
-- in two months is counted in both rows).


-- Q16. New (first-observed) users by month ------------------------------
-- Grain: one row per month.
-- "New" means first seen INSIDE this 3-month sample. Many November "new"
-- users will really be returning visitors whose earlier history is simply
-- outside the sample.
WITH first_seen AS (
  SELECT user_pseudo_id, MIN(event_dt) AS first_seen_dt
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
)
SELECT
  DATE_TRUNC(first_seen_dt, MONTH)   AS first_seen_month,
  COUNT(*)                           AS first_observed_users,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_all_users
FROM first_seen
GROUP BY first_seen_month
ORDER BY first_seen_month;


-- Q17. Session-level engagement summary ---------------------------------
-- Grain: one row per device category. Unit = SESSION.
SELECT
  device_category,
  COUNT(*)                                        AS sessions,
  COUNT(DISTINCT user_pseudo_id)                  AS users,
  ROUND(SAFE_DIVIDE(COUNT(*), COUNT(DISTINCT user_pseudo_id)), 2) AS sessions_per_user,
  ROUND(AVG(events), 1)                           AS avg_events_per_session,
  ROUND(AVG(page_views), 1)                       AS avg_page_views_per_session,
  ROUND(APPROX_QUANTILES(engagement_sec, 2)[OFFSET(1)], 1) AS median_engagement_sec,
  ROUND(SAFE_DIVIDE(COUNTIF(purchased = 1), COUNT(*)), 4)  AS session_purchase_rate
FROM `YOUR_PROJECT.productpulse.sessions_base`
GROUP BY device_category
ORDER BY sessions DESC;


-- Q18. 7-day rolling average of daily active users (window function) ----
-- Grain: one row per day.
-- Smooths weekday/weekend swings so the trend is readable.
-- Note: this averages daily counts; it is NOT "weekly active users".
WITH daily AS (
  SELECT event_dt, COUNT(DISTINCT user_pseudo_id) AS active_users
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY event_dt
)
SELECT
  event_dt,
  active_users,
  ROUND(AVG(active_users) OVER (
    ORDER BY event_dt ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS active_users_7d_avg,
  active_users - LAG(active_users, 7) OVER (ORDER BY event_dt)      AS change_vs_same_day_last_week
FROM daily
ORDER BY event_dt;
