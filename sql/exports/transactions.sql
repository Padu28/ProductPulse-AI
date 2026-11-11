-- EXPORT: transactions.csv | Grain: one row per validated transaction_id.
-- Used by the data-quality notebook to check duplicates and revenue.
SELECT
  transaction_id,
  MIN(event_dt)                    AS purchase_dt,
  MIN(device_category)             AS device_category,
  COUNT(*)                         AS purchase_events,
  COUNT(DISTINCT user_pseudo_id)   AS distinct_users,
  MAX(purchase_revenue_usd)        AS revenue_usd,
  MIN(purchase_revenue_usd)        AS min_revenue_usd,
  MAX(total_item_quantity)         AS total_item_quantity
FROM `YOUR_PROJECT.productpulse.events_base`
WHERE event_name = 'purchase'
  AND user_pseudo_id IS NOT NULL
  AND transaction_id IS NOT NULL
  AND transaction_id != '(not set)'
GROUP BY transaction_id
ORDER BY purchase_dt, transaction_id;
