-- EXPORT: cohort_retention_monthly.csv | Grain: cohort_month x month_number. Unit = USER.
-- Same logic as Q23. Periods after the sample ends are absent rows, not zeros.
WITH first_seen AS (
  SELECT user_pseudo_id, DATE_TRUNC(MIN(event_dt), MONTH) AS cohort_month
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
),
user_months AS (
  SELECT DISTINCT user_pseudo_id, DATE_TRUNC(event_dt, MONTH) AS activity_month
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
