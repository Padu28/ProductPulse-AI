-- =====================================================================
-- ProductPulse AI | 06_product_analysis.sql
-- Purpose : Which products are viewed, added to cart and bought?
-- Requires: the views from 00_create_views.sql.
--
-- items_base has ITEM-LEVEL grain (one row per event x item). Every query
-- here states its unit. User counts use COUNT(DISTINCT user_pseudo_id), and
-- order counts use COUNT(DISTINCT transaction_id), so the row multiplication
-- from UNNEST cannot inflate them.
-- =====================================================================


-- Q27. Product performance table -----------------------------------------
-- Grain: one row per item_name.
-- Item-level "view to purchase" compares users who viewed an item with
-- users who bought the SAME item at any time in the sample. It is an
-- association, not proof that the view led to the purchase.
SELECT
  item_name,
  ANY_VALUE(item_category)                                                    AS item_category,
  COUNTIF(event_name = 'view_item')                                           AS view_item_rows,
  COUNT(DISTINCT IF(event_name = 'view_item',   user_pseudo_id, NULL))        AS users_viewed,
  COUNT(DISTINCT IF(event_name = 'add_to_cart', user_pseudo_id, NULL))        AS users_added_cart,
  COUNT(DISTINCT IF(event_name = 'purchase',    user_pseudo_id, NULL))        AS users_purchased,
  COUNT(DISTINCT IF(event_name = 'purchase'
                    AND transaction_id IS NOT NULL
                    AND transaction_id != '(not set)', transaction_id, NULL)) AS orders,
  SUM(IF(event_name = 'purchase', quantity, 0))                               AS units_purchased,
  ROUND(SUM(IF(event_name = 'purchase', item_revenue_in_usd, 0)), 2)          AS item_revenue_usd,
  ROUND(SAFE_DIVIDE(
    COUNT(DISTINCT IF(event_name = 'purchase',  user_pseudo_id, NULL)),
    COUNT(DISTINCT IF(event_name = 'view_item', user_pseudo_id, NULL))), 4)   AS viewer_to_buyer_rate
FROM `YOUR_PROJECT.productpulse.items_base`
WHERE item_name IS NOT NULL
  AND item_name != '(not set)'
GROUP BY item_name
ORDER BY users_viewed DESC;
-- Caveat: units and item revenue sum purchase rows as exported. If Q11 shows
-- orders with repeated purchase events, treat item revenue as approximate
-- and prefer the de-duplicated order revenue for headline numbers.


-- Q28. Category performance ----------------------------------------------
-- Grain: one row per item_category.
SELECT
  IFNULL(NULLIF(item_category, ''), '(not set)')                              AS item_category,
  COUNT(DISTINCT item_name)                                                   AS distinct_items,
  COUNT(DISTINCT IF(event_name = 'view_item',   user_pseudo_id, NULL))        AS users_viewed,
  COUNT(DISTINCT IF(event_name = 'add_to_cart', user_pseudo_id, NULL))        AS users_added_cart,
  COUNT(DISTINCT IF(event_name = 'purchase',    user_pseudo_id, NULL))        AS users_purchased,
  SUM(IF(event_name = 'purchase', quantity, 0))                               AS units_purchased,
  ROUND(SUM(IF(event_name = 'purchase', item_revenue_in_usd, 0)), 2)          AS item_revenue_usd
FROM `YOUR_PROJECT.productpulse.items_base`
GROUP BY 1
ORDER BY users_viewed DESC;


-- Q29. High interest, low purchase: products to investigate --------------
-- Grain: one row per item_name (items with at least 500 viewing users).
-- Ranks items inside each category by viewer-to-buyer rate (window function).
-- A low rate is a prompt to investigate (price, stock, page content);
-- the data cannot say WHY.
WITH item_stats AS (
  SELECT
    item_name,
    ANY_VALUE(item_category)                                            AS item_category,
    COUNT(DISTINCT IF(event_name = 'view_item', user_pseudo_id, NULL))  AS users_viewed,
    COUNT(DISTINCT IF(event_name = 'purchase',  user_pseudo_id, NULL))  AS users_purchased
  FROM `YOUR_PROJECT.productpulse.items_base`
  WHERE item_name IS NOT NULL AND item_name != '(not set)'
  GROUP BY item_name
)
SELECT
  item_category,
  item_name,
  users_viewed,
  users_purchased,
  ROUND(SAFE_DIVIDE(users_purchased, users_viewed), 4)  AS viewer_to_buyer_rate,
  RANK() OVER (
    PARTITION BY item_category
    ORDER BY SAFE_DIVIDE(users_purchased, users_viewed)) AS rank_lowest_in_category
FROM item_stats
WHERE users_viewed >= 500
ORDER BY viewer_to_buyer_rate
LIMIT 25;


-- Q30. Order size distribution -------------------------------------------
-- Grain: one row per order-value bucket. Unit = validated ORDER.
WITH tx AS (
  SELECT
    transaction_id,
    MAX(purchase_revenue_usd)  AS revenue_usd,
    MAX(total_item_quantity)   AS items_in_order
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE event_name = 'purchase'
    AND transaction_id IS NOT NULL
    AND transaction_id != '(not set)'
  GROUP BY transaction_id
)
SELECT
  CASE
    WHEN revenue_usd IS NULL OR revenue_usd = 0 THEN 'a) $0 or missing'
    WHEN revenue_usd < 25  THEN 'b) under $25'
    WHEN revenue_usd < 50  THEN 'c) $25-49'
    WHEN revenue_usd < 100 THEN 'd) $50-99'
    WHEN revenue_usd < 200 THEN 'e) $100-199'
    ELSE 'f) $200+'
  END                                 AS order_value_bucket,
  COUNT(*)                            AS orders,
  ROUND(SUM(revenue_usd), 2)          AS revenue_usd,
  ROUND(AVG(items_in_order), 1)       AS avg_items_in_order
FROM tx
GROUP BY order_value_bucket
ORDER BY order_value_bucket;
