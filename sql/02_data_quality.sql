-- =====================================================================
-- ProductPulse AI | 02_data_quality.sql
-- Purpose : Find nulls, duplicates and odd values, and record a handling
--           rule for each one in data/data_dictionary.md.
-- Requires: the views from 00_create_views.sql.
-- =====================================================================


-- Q07. Null and missing-value check on the key fields -------------------
-- Grain: one row for the whole sample.
-- Rule : rows with a null user_pseudo_id are EXCLUDED from every
--        distinct-user metric; rows with a null ga_session_id are excluded
--        from session metrics. This query tells you how many that is.
SELECT
  COUNT(*)                                   AS event_rows,
  COUNTIF(user_pseudo_id IS NULL)            AS null_user_id_rows,
  COUNTIF(ga_session_id IS NULL)             AS null_session_id_rows,
  COUNTIF(event_name IS NULL)                AS null_event_name_rows,
  COUNTIF(device_category IS NULL)           AS null_device_rows,
  COUNTIF(country IS NULL OR country = '')   AS null_country_rows,
  COUNTIF(country = '(not set)')             AS not_set_country_rows,
  COUNTIF(first_user_source IS NULL)         AS null_source_rows,
  COUNTIF(first_user_source = '(data deleted)') AS data_deleted_source_rows,
  COUNTIF(first_user_source = '<Other>')     AS other_source_rows
FROM `YOUR_PROJECT.productpulse.events_base`;


-- Q08. Exact duplicate events -------------------------------------------
-- Grain: one row per duplicated (user, timestamp, event, session) key.
-- GA4 exports have no event id, so "duplicate" here means the same user
-- firing the same event name in the same microsecond. Some are legitimate
-- (e.g. several view_item events batched together), so we REPORT them but
-- do not delete them. User- and session-level metrics are unaffected
-- because they use DISTINCT.
SELECT
  user_pseudo_id,
  event_timestamp,
  event_name,
  ga_session_id,
  COUNT(*) AS copies
FROM `YOUR_PROJECT.productpulse.events_base`
GROUP BY 1, 2, 3, 4
HAVING COUNT(*) > 1
ORDER BY copies DESC
LIMIT 100;


-- Q09. How big is the duplicate issue, by event name? -------------------
-- Grain: one row per event_name.
WITH keyed AS (
  SELECT event_name, user_pseudo_id, event_timestamp, ga_session_id, COUNT(*) AS copies
  FROM `YOUR_PROJECT.productpulse.events_base`
  GROUP BY 1, 2, 3, 4
)
SELECT
  event_name,
  SUM(copies)                               AS event_rows,
  SUM(copies - 1)                           AS extra_copies,
  ROUND(100 * SAFE_DIVIDE(SUM(copies - 1), SUM(copies)), 3) AS pct_extra
FROM keyed
GROUP BY event_name
ORDER BY extra_copies DESC;


-- Q10. Timestamp sanity --------------------------------------------------
-- Grain: one row for the whole sample.
-- event_date is in the property's reporting time zone, event_timestamp is
-- UTC, so a small number of mismatches around midnight is expected.
SELECT
  MIN(event_ts)                                         AS earliest_event_ts_utc,
  MAX(event_ts)                                         AS latest_event_ts_utc,
  COUNTIF(event_timestamp IS NULL)                      AS null_timestamps,
  COUNTIF(DATE(event_ts) != event_dt)                   AS rows_where_utc_date_differs,
  ROUND(100 * COUNTIF(DATE(event_ts) != event_dt) / COUNT(*), 2) AS pct_utc_date_differs,
  COUNTIF(event_dt < '2020-11-01' OR event_dt > '2021-01-31')    AS rows_outside_period
FROM `YOUR_PROJECT.productpulse.events_base`;


-- Q11. Purchase and revenue validation ----------------------------------
-- Grain: one row for the whole sample.
-- Decides the rule for "validated orders":
--   an order = a DISTINCT transaction_id that is not null and not '(not set)'.
-- Revenue field used: ecommerce.purchase_revenue_in_usd (USD).
WITH purchases AS (
  SELECT transaction_id, purchase_revenue_usd, user_pseudo_id
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE event_name = 'purchase'
),
per_tx AS (
  SELECT
    transaction_id,
    COUNT(*)                          AS purchase_events,
    COUNT(DISTINCT user_pseudo_id)    AS users,
    MAX(purchase_revenue_usd)         AS max_revenue,
    MIN(purchase_revenue_usd)         AS min_revenue
  FROM purchases
  WHERE transaction_id IS NOT NULL AND transaction_id != '(not set)'
  GROUP BY transaction_id
)
SELECT
  (SELECT COUNT(*) FROM purchases)                                              AS purchase_events,
  (SELECT COUNTIF(transaction_id IS NULL) FROM purchases)                       AS null_transaction_id,
  (SELECT COUNTIF(transaction_id = '(not set)') FROM purchases)                 AS not_set_transaction_id,
  (SELECT COUNTIF(purchase_revenue_usd IS NULL) FROM purchases)                 AS null_revenue,
  (SELECT COUNTIF(purchase_revenue_usd = 0) FROM purchases)                     AS zero_revenue,
  (SELECT COUNTIF(purchase_revenue_usd < 0) FROM purchases)                     AS negative_revenue,
  (SELECT COUNT(*) FROM per_tx)                                                 AS validated_orders,
  (SELECT COUNTIF(purchase_events > 1) FROM per_tx)                             AS orders_with_repeat_events,
  (SELECT COUNTIF(users > 1) FROM per_tx)                                       AS orders_shared_by_users,
  (SELECT COUNTIF(max_revenue != min_revenue) FROM per_tx)                      AS orders_with_conflicting_revenue,
  (SELECT ROUND(SUM(purchase_revenue_usd), 2) FROM purchases)                   AS revenue_summing_every_event,
  (SELECT ROUND(SUM(max_revenue), 2) FROM per_tx)                               AS revenue_deduplicated;
-- If the last two numbers differ, summing raw purchase events double counts.
-- This project always reports `revenue_deduplicated`.


-- Q12. Does unnesting items multiply rows? ------------------------------
-- Grain: one row per funnel event name.
-- Compares the event count with the row count after UNNEST(items) so you
-- can see exactly how much item-level analysis inflates row counts.
SELECT
  e.event_name,
  COUNT(*)                         AS events,
  SUM(ARRAY_LENGTH(e.items))       AS rows_after_unnest,
  ROUND(SAFE_DIVIDE(SUM(ARRAY_LENGTH(e.items)), COUNT(*)), 2) AS avg_items_per_event,
  COUNTIF(ARRAY_LENGTH(e.items) = 0) AS events_with_no_items
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` AS e
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
  AND e.event_name IN ('view_item', 'add_to_cart', 'begin_checkout', 'purchase')
GROUP BY e.event_name
ORDER BY events DESC;


-- Q13. Do users appear with more than one device or country? ------------
-- Grain: one row for the whole sample.
-- Matters because dim_user assigns each user ONE device and country
-- (the first observed). This shows how many users that simplifies.
WITH per_user AS (
  SELECT
    user_pseudo_id,
    COUNT(DISTINCT device_category) AS devices,
    COUNT(DISTINCT country)         AS countries
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
)
SELECT
  COUNT(*)                      AS users,
  COUNTIF(devices > 1)          AS users_with_multiple_devices,
  COUNTIF(countries > 1)        AS users_with_multiple_countries,
  ROUND(100 * COUNTIF(devices > 1) / COUNT(*), 2)   AS pct_multiple_devices,
  ROUND(100 * COUNTIF(countries > 1) / COUNT(*), 2) AS pct_multiple_countries
FROM per_user;
