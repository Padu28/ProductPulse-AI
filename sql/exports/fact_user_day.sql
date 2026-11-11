-- EXPORT: fact_user_day.csv | Grain: one row per user_pseudo_id x event_dt (fact table).
-- This is the table Power BI and the notebooks use, because distinct users
-- can be counted correctly under ANY date / device / country / channel filter.
-- Orders and revenue are de-duplicated by transaction_id and assigned to the
-- user and day of the order's first purchase event.
-- Contains the obfuscated user_pseudo_id: keep this file local (git-ignored).
WITH activity AS (
  SELECT
    user_pseudo_id,
    event_dt,
    COUNT(*)                                        AS events,
    COUNT(DISTINCT ga_session_id)                   AS sessions,
    COUNTIF(event_name = 'page_view')               AS page_views,
    ROUND(SUM(IFNULL(engagement_time_msec, 0)) / 1000, 1) AS engagement_sec,
    MAX(IF(event_name = 'view_item', 1, 0))         AS viewed_item,
    MAX(IF(event_name = 'add_to_cart', 1, 0))       AS added_cart,
    MAX(IF(event_name = 'begin_checkout', 1, 0))    AS began_checkout,
    MAX(IF(event_name = 'purchase', 1, 0))          AS purchased
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id, event_dt
),
tx AS (
  SELECT
    transaction_id,
    ARRAY_AGG(user_pseudo_id ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS user_pseudo_id,
    MIN(event_dt)              AS event_dt,
    MAX(purchase_revenue_usd)  AS revenue_usd
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE event_name = 'purchase'
    AND user_pseudo_id IS NOT NULL
    AND transaction_id IS NOT NULL
    AND transaction_id != '(not set)'
  GROUP BY transaction_id
),
user_day_tx AS (
  SELECT user_pseudo_id, event_dt, COUNT(*) AS transactions, SUM(revenue_usd) AS revenue_usd
  FROM tx
  GROUP BY user_pseudo_id, event_dt
)
SELECT
  a.user_pseudo_id,
  a.event_dt,
  a.events,
  a.sessions,
  a.page_views,
  a.engagement_sec,
  a.viewed_item,
  a.added_cart,
  a.began_checkout,
  a.purchased,
  IFNULL(t.transactions, 0)           AS transactions,
  ROUND(IFNULL(t.revenue_usd, 0), 2)  AS revenue_usd
FROM activity AS a
LEFT JOIN user_day_tx AS t USING (user_pseudo_id, event_dt);
