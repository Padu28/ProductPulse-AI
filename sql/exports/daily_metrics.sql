-- EXPORT: daily_metrics.csv | Grain: one row per day. Same logic as Q14.
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
  SELECT transaction_id, MIN(event_dt) AS purchase_dt, MAX(purchase_revenue_usd) AS revenue_usd
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
  IFNULL(t.transactions, 0)           AS transactions,
  ROUND(IFNULL(t.revenue_usd, 0), 2)  AS revenue_usd
FROM daily AS d
LEFT JOIN daily_tx AS t ON t.purchase_dt = d.event_dt
ORDER BY d.event_dt;
