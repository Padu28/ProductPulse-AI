-- EXPORT: session_funnel.csv | Grain: device_category x channel_group. Unit = SESSION.
-- Sequential funnel inside one session, same logic as Q21 / Q33.
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
  IFNULL(device_category, '(not set)')  AS device_category,
  channel_group,
  COUNT(*)                         AS sessions,
  COUNTIF(t_view IS NOT NULL)      AS seq_view,
  COUNTIF(t_cart IS NOT NULL)      AS seq_cart,
  COUNTIF(t_checkout IS NOT NULL)  AS seq_checkout,
  COUNTIF(t_purchase IS NOT NULL)  AS seq_purchase,
  COUNTIF(any_purchase = 1)        AS any_purchase
FROM per_session
GROUP BY 1, 2
ORDER BY sessions DESC;
