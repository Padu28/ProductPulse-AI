-- EXPORT: product_performance.csv | Grain: one row per item_name. Same logic as Q27.
SELECT
  item_name,
  ANY_VALUE(item_category)                                                    AS item_category,
  COUNT(DISTINCT IF(event_name = 'view_item',   user_pseudo_id, NULL))        AS users_viewed,
  COUNT(DISTINCT IF(event_name = 'add_to_cart', user_pseudo_id, NULL))        AS users_added_cart,
  COUNT(DISTINCT IF(event_name = 'purchase',    user_pseudo_id, NULL))        AS users_purchased,
  COUNT(DISTINCT IF(event_name = 'purchase'
                    AND transaction_id IS NOT NULL
                    AND transaction_id != '(not set)', transaction_id, NULL)) AS orders,
  SUM(IF(event_name = 'purchase', quantity, 0))                               AS units_purchased,
  ROUND(SUM(IF(event_name = 'purchase', item_revenue_in_usd, 0)), 2)          AS item_revenue_usd
FROM `YOUR_PROJECT.productpulse.items_base`
WHERE item_name IS NOT NULL
  AND item_name != '(not set)'
GROUP BY item_name
ORDER BY users_viewed DESC;
