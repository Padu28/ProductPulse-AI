-- =====================================================================
-- ProductPulse AI | 01_schema_exploration.sql
-- Purpose : Understand the dataset BEFORE calculating any metric.
-- Run each query on its own (highlight it, then Run). Check the cost
-- estimate in the top-right of the BigQuery editor first.
-- These queries read the public tables directly, so no setup is needed.
-- =====================================================================


-- Q01. Date coverage and overall size ---------------------------------
-- Grain: one row for the whole sample.
-- Expect: first date 20201101, last date 20210131.
SELECT
  MIN(event_date)                 AS first_event_date,
  MAX(event_date)                 AS last_event_date,
  COUNT(DISTINCT event_date)      AS days_with_data,      -- expect 92
  COUNT(*)                        AS event_rows,
  COUNT(DISTINCT user_pseudo_id)  AS identified_users
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131';


-- Q02. Event names: how many rows and users for each? ------------------
-- Grain: one row per event_name.
-- Use this to decide which events map to funnel stages.
SELECT
  event_name,
  COUNT(*)                        AS event_rows,
  COUNT(DISTINCT user_pseudo_id)  AS users,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_all_events
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY event_name
ORDER BY event_rows DESC;


-- Q03. Which event_params keys exist, and what value type do they use? -
-- Grain: one row per parameter key.
-- This query intentionally unnests (one row per event x parameter), so
-- `occurrences` is a count of parameters, NOT a count of events.
SELECT
  ep.key,
  COUNT(*)                                AS occurrences,
  COUNTIF(ep.value.string_value IS NOT NULL) AS string_values,
  COUNTIF(ep.value.int_value    IS NOT NULL) AS int_values,
  COUNTIF(ep.value.float_value  IS NOT NULL) AS float_values,
  COUNTIF(ep.value.double_value IS NOT NULL) AS double_values
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
     UNNEST(event_params) AS ep
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY ep.key
ORDER BY occurrences DESC;


-- Q04. Look at real values for the session keys ------------------------
-- A cheap peek at one day, to confirm ga_session_id is an integer and
-- page_location is a string before the views rely on that.
SELECT
  event_name,
  user_pseudo_id,
  (SELECT ep.value.int_value    FROM UNNEST(event_params) ep WHERE ep.key = 'ga_session_id')     AS ga_session_id,
  (SELECT ep.value.int_value    FROM UNNEST(event_params) ep WHERE ep.key = 'ga_session_number') AS ga_session_number,
  (SELECT ep.value.string_value FROM UNNEST(event_params) ep WHERE ep.key = 'page_location')     AS page_location
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_20201101`
LIMIT 50;


-- Q05. Device, country and traffic-source values ------------------------
-- Grain: one row per value of each dimension (stacked with UNION ALL).
-- Look for nulls, '(not set)', '<Other>' and '(data deleted)' so you can
-- document how each is handled.
WITH base AS (
  SELECT
    user_pseudo_id,
    device.category        AS device_category,
    geo.country            AS country,
    traffic_source.source  AS source,
    traffic_source.medium  AS medium
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
)
SELECT 'device_category' AS dimension, IFNULL(device_category, '(null)') AS value,
       COUNT(*) AS event_rows, COUNT(DISTINCT user_pseudo_id) AS users
FROM base GROUP BY 2
UNION ALL
SELECT 'source', IFNULL(source, '(null)'), COUNT(*), COUNT(DISTINCT user_pseudo_id)
FROM base GROUP BY 2
UNION ALL
SELECT 'medium', IFNULL(medium, '(null)'), COUNT(*), COUNT(DISTINCT user_pseudo_id)
FROM base GROUP BY 2
UNION ALL
SELECT 'country', IFNULL(country, '(null)'), COUNT(*), COUNT(DISTINCT user_pseudo_id)
FROM base GROUP BY 2
ORDER BY dimension, event_rows DESC;


-- Q06. What does the items array look like on a purchase event? ---------
-- Grain: one row per purchase event x item (intentional unnest).
-- Confirms which item fields are populated before product analysis.
SELECT
  e.event_date,
  e.ecommerce.transaction_id,
  e.ecommerce.purchase_revenue_in_usd,
  ARRAY_LENGTH(e.items)   AS items_in_event,
  it.item_id,
  it.item_name,
  it.item_category,
  it.price_in_usd,
  it.quantity,
  it.item_revenue_in_usd
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_20201201` AS e,
     UNNEST(e.items) AS it
WHERE e.event_name = 'purchase'
LIMIT 50;
