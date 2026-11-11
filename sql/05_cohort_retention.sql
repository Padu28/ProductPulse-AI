-- =====================================================================
-- ProductPulse AI | 05_cohort_retention.sql
-- Purpose : Do users come back? Monthly and weekly activity retention.
-- Requires: the views from 00_create_views.sql.
--
-- Definitions
--   Cohort     = the month (or week) of a user's FIRST OBSERVED event in
--                the sample. It is not necessarily their true first visit.
--   Retained   = the user fired at least one event (any event, not a
--                purchase) in the later period.
--   Incomplete = the sample ends 2021-01-31, so later cohorts have fewer
--                periods to be observed in. Missing periods are ABSENT rows
--                (blank), never zero.
-- =====================================================================


-- Q23. Monthly activity retention ----------------------------------------
-- Grain: one row per cohort_month x month_number. Unit = USER.
WITH first_seen AS (
  SELECT
    user_pseudo_id,
    DATE_TRUNC(MIN(event_dt), MONTH) AS cohort_month
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
),
user_months AS (
  SELECT DISTINCT
    user_pseudo_id,
    DATE_TRUNC(event_dt, MONTH) AS activity_month
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
),
cohort_activity AS (
  SELECT
    f.cohort_month,
    DATE_DIFF(u.activity_month, f.cohort_month, MONTH) AS month_number,
    COUNT(DISTINCT u.user_pseudo_id)                   AS active_users
  FROM first_seen AS f
  JOIN user_months AS u USING (user_pseudo_id)
  GROUP BY 1, 2
),
cohort_size AS (
  SELECT cohort_month, active_users AS cohort_users
  FROM cohort_activity
  WHERE month_number = 0
)
SELECT
  a.cohort_month,
  a.month_number,
  a.active_users,
  s.cohort_users,
  ROUND(SAFE_DIVIDE(a.active_users, s.cohort_users), 4) AS retention_rate
FROM cohort_activity AS a
JOIN cohort_size AS s USING (cohort_month)
ORDER BY a.cohort_month, a.month_number;

-- Validation for Q23: month_number = 0 must always be 100%, and the sum of
-- cohort_users across cohorts must equal identified_users from Q01.


-- Q24. Weekly activity retention (first 8 weeks) -------------------------
-- Grain: one row per cohort_week x week_number. Unit = USER.
-- Weeks start on Monday. Weekly cohorts give more data points than three
-- monthly cohorts, but late cohorts are still incomplete.
WITH first_seen AS (
  SELECT
    user_pseudo_id,
    DATE_TRUNC(MIN(event_dt), WEEK(MONDAY)) AS cohort_week
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
),
user_weeks AS (
  SELECT DISTINCT
    user_pseudo_id,
    DATE_TRUNC(event_dt, WEEK(MONDAY)) AS activity_week
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
),
cohort_activity AS (
  SELECT
    f.cohort_week,
    DATE_DIFF(u.activity_week, f.cohort_week, WEEK(MONDAY)) AS week_number,
    COUNT(DISTINCT u.user_pseudo_id)                        AS active_users
  FROM first_seen AS f
  JOIN user_weeks AS u USING (user_pseudo_id)
  GROUP BY 1, 2
)
SELECT
  cohort_week,
  week_number,
  active_users,
  FIRST_VALUE(active_users) OVER (
    PARTITION BY cohort_week ORDER BY week_number)          AS cohort_users,
  ROUND(SAFE_DIVIDE(
    active_users,
    FIRST_VALUE(active_users) OVER (
      PARTITION BY cohort_week ORDER BY week_number)), 4)   AS retention_rate
FROM cohort_activity
WHERE week_number <= 8
ORDER BY cohort_week, week_number;


-- Q25. Repeat activity: on how many separate days was each user active? --
-- Grain: one row per bucket of active days. Unit = USER.
-- "Repeat activity" means returning on another day. It does NOT mean a
-- repeat purchase.
WITH per_user AS (
  SELECT
    user_pseudo_id,
    COUNT(DISTINCT event_dt) AS active_days
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
)
SELECT
  CASE
    WHEN active_days = 1 THEN '1 day only'
    WHEN active_days = 2 THEN '2 days'
    WHEN active_days BETWEEN 3 AND 5 THEN '3-5 days'
    ELSE '6+ days'
  END                                              AS active_days_bucket,
  MIN(active_days)                                 AS sort_key,
  COUNT(*)                                         AS users,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_users
FROM per_user
GROUP BY active_days_bucket
ORDER BY sort_key;


-- Q26. Repeat purchasers --------------------------------------------------
-- Grain: one row for the whole sample. Unit = USER with a validated order.
WITH orders AS (
  SELECT
    user_pseudo_id,
    COUNT(DISTINCT transaction_id) AS orders
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE event_name = 'purchase'
    AND user_pseudo_id IS NOT NULL
    AND transaction_id IS NOT NULL
    AND transaction_id != '(not set)'
  GROUP BY user_pseudo_id
)
SELECT
  COUNT(*)                                             AS purchasers,
  COUNTIF(orders >= 2)                                 AS repeat_purchasers,
  ROUND(SAFE_DIVIDE(COUNTIF(orders >= 2), COUNT(*)), 4) AS repeat_purchase_rate,
  MAX(orders)                                          AS max_orders_by_one_user
FROM orders;
