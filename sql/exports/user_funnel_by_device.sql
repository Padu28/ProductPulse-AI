-- EXPORT: user_funnel_by_device.csv | Grain: one row per device. Unit = USER.
-- Stage-presence funnel, same logic as Q20. Used to reconcile Python and
-- Power BI against SQL.
WITH ranked AS (
  SELECT
    user_pseudo_id,
    device_category,
    ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY event_timestamp, event_name) AS rn
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
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
  IFNULL(d.device_category, '(not set)')  AS device_category,
  COUNT(*)                                AS users,
  COUNTIF(s.viewed_item = 1)              AS users_viewed,
  COUNTIF(s.added_cart = 1)               AS users_added_cart,
  COUNTIF(s.began_checkout = 1)           AS users_began_checkout,
  COUNTIF(s.purchased = 1)                AS users_purchased
FROM user_stage AS s
JOIN ranked AS d ON d.user_pseudo_id = s.user_pseudo_id AND d.rn = 1
GROUP BY 1
ORDER BY users DESC;
