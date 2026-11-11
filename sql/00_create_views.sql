-- =====================================================================
-- ProductPulse AI | 00_create_views.sql
-- Purpose : Create the three reusable views every other query reads from.
-- Source  : bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*
-- Period  : 2020-11-01 to 2021-01-31 (the full public sample)
--
-- BEFORE RUNNING
--   1. In BigQuery, create a dataset called `productpulse` in the US
--      multi-region (the public dataset lives in US).
--   2. Replace YOUR_PROJECT with your Google Cloud project ID.
--      (scripts/export_from_bigquery.py does both steps for you.)
--
-- Why views? One place defines the date range, the null handling and the
-- event_params extraction, so every metric uses identical rules.
-- =====================================================================


-- ---------------------------------------------------------------------
-- VIEW 1: events_base
-- Grain : one row per GA4 event (same row count as the filtered source).
-- Note  : event_params is a repeated key/value field. Each parameter is
--         pulled out with a scalar sub-query, which returns ONE value per
--         event and therefore cannot multiply rows (a plain
--         CROSS JOIN UNNEST would).
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW `YOUR_PROJECT.productpulse.events_base` AS
SELECT
  PARSE_DATE('%Y%m%d', event_date)                      AS event_dt,
  event_timestamp,                                      -- microseconds since epoch (UTC)
  TIMESTAMP_MICROS(event_timestamp)                     AS event_ts,
  event_name,
  user_pseudo_id,

  -- Session fields live inside event_params as integers.
  (SELECT ep.value.int_value
     FROM UNNEST(event_params) AS ep
    WHERE ep.key = 'ga_session_id')                     AS ga_session_id,
  (SELECT ep.value.int_value
     FROM UNNEST(event_params) AS ep
    WHERE ep.key = 'ga_session_number')                 AS ga_session_number,
  (SELECT ep.value.int_value
     FROM UNNEST(event_params) AS ep
    WHERE ep.key = 'engagement_time_msec')              AS engagement_time_msec,
  (SELECT ep.value.string_value
     FROM UNNEST(event_params) AS ep
    WHERE ep.key = 'page_location')                     AS page_location,
  (SELECT ep.value.string_value
     FROM UNNEST(event_params) AS ep
    WHERE ep.key = 'page_title')                        AS page_title,

  -- Context dimensions
  device.category                                       AS device_category,
  device.operating_system                               AS operating_system,
  device.web_info.browser                               AS browser,
  geo.country                                           AS country,

  -- traffic_source is USER-level first-touch attribution in the GA4 export
  -- (the source that first acquired the user), not the source of each session.
  traffic_source.source                                 AS first_user_source,
  traffic_source.medium                                 AS first_user_medium,
  traffic_source.name                                   AS first_user_campaign,
  CASE
    WHEN traffic_source.source = '(data deleted)'
      OR traffic_source.medium = '(data deleted)'             THEN 'Data deleted'
    WHEN traffic_source.source = '(direct)'
     AND traffic_source.medium IN ('(none)', '(not set)')     THEN 'Direct'
    WHEN traffic_source.medium = 'organic'                    THEN 'Organic search'
    WHEN traffic_source.medium IN ('cpc', 'ppc', 'paid')      THEN 'Paid search'
    WHEN traffic_source.medium = 'referral'                   THEN 'Referral'
    WHEN traffic_source.source IS NULL
     AND traffic_source.medium IS NULL                        THEN 'Unknown'
    ELSE 'Other'
  END                                                   AS channel_group,

  -- Ecommerce fields (populated mainly on purchase events)
  ecommerce.transaction_id                              AS transaction_id,
  ecommerce.purchase_revenue_in_usd                     AS purchase_revenue_usd,
  ecommerce.total_item_quantity                         AS total_item_quantity
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131';


-- ---------------------------------------------------------------------
-- VIEW 2: items_base
-- Grain : one row per event x item (item-level grain).
-- WARNING: this view deliberately multiplies event rows (one per item in
--          the items array). Never count events, users or revenue totals
--          from it without re-aggregating to the grain you intend.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW `YOUR_PROJECT.productpulse.items_base` AS
SELECT
  PARSE_DATE('%Y%m%d', e.event_date)                    AS event_dt,
  e.event_timestamp,
  e.event_name,
  e.user_pseudo_id,
  (SELECT ep.value.int_value
     FROM UNNEST(e.event_params) AS ep
    WHERE ep.key = 'ga_session_id')                     AS ga_session_id,
  e.device.category                                     AS device_category,
  e.ecommerce.transaction_id                            AS transaction_id,
  it.item_id,
  it.item_name,
  it.item_category,
  it.item_brand,
  it.price_in_usd,
  it.quantity,
  it.item_revenue_in_usd
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` AS e,
     UNNEST(e.items) AS it
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
  AND e.event_name IN ('view_item', 'add_to_cart', 'begin_checkout', 'purchase');


-- ---------------------------------------------------------------------
-- VIEW 3: sessions_base
-- Grain : one row per session, where a session = user_pseudo_id + ga_session_id.
--         (ga_session_id alone is NOT unique across users.)
-- Rows without a user id or session id are excluded and counted in
-- sql/02_data_quality.sql.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW `YOUR_PROJECT.productpulse.sessions_base` AS
SELECT
  user_pseudo_id,
  ga_session_id,
  CONCAT(user_pseudo_id, '-', CAST(ga_session_id AS STRING)) AS session_key,
  MIN(event_dt)                                         AS session_dt,
  MIN(event_timestamp)                                  AS session_start_ts,
  MAX(event_timestamp)                                  AS session_end_ts,
  MAX(ga_session_number)                                AS ga_session_number,
  MIN(device_category)                                  AS device_category,
  MIN(country)                                          AS country,
  MIN(channel_group)                                    AS channel_group,
  COUNT(*)                                              AS events,
  COUNTIF(event_name = 'page_view')                     AS page_views,
  SUM(IFNULL(engagement_time_msec, 0)) / 1000           AS engagement_sec,
  MAX(IF(event_name = 'view_item', 1, 0))               AS viewed_item,
  MAX(IF(event_name = 'add_to_cart', 1, 0))             AS added_cart,
  MAX(IF(event_name = 'begin_checkout', 1, 0))          AS began_checkout,
  MAX(IF(event_name = 'purchase', 1, 0))                AS purchased
FROM `YOUR_PROJECT.productpulse.events_base`
WHERE user_pseudo_id IS NOT NULL
  AND ga_session_id IS NOT NULL
GROUP BY user_pseudo_id, ga_session_id;
