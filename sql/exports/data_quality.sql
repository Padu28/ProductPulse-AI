-- EXPORT: data_quality.csv | Grain: one row per quality check (long format).
WITH e AS (
  SELECT * FROM `YOUR_PROJECT.productpulse.events_base`
),
dup AS (
  SELECT SUM(copies - 1) AS extra_copies
  FROM (
    SELECT COUNT(*) AS copies
    FROM e
    GROUP BY user_pseudo_id, event_timestamp, event_name, ga_session_id
  )
),
p AS (
  SELECT * FROM e WHERE event_name = 'purchase'
),
per_tx AS (
  SELECT transaction_id, COUNT(*) AS n, MAX(purchase_revenue_usd) AS rev
  FROM p
  WHERE transaction_id IS NOT NULL AND transaction_id != '(not set)'
  GROUP BY transaction_id
)
SELECT 'event_rows' AS check_name, CAST(COUNT(*) AS FLOAT64) AS value, 'All rows in events_base' AS note FROM e
UNION ALL SELECT 'null_user_id_rows', COUNTIF(user_pseudo_id IS NULL), 'Excluded from user metrics' FROM e
UNION ALL SELECT 'null_session_id_rows', COUNTIF(ga_session_id IS NULL), 'Excluded from session metrics' FROM e
UNION ALL SELECT 'null_device_rows', COUNTIF(device_category IS NULL), 'Shown as (not set)' FROM e
UNION ALL SELECT 'not_set_country_rows', COUNTIF(country IS NULL OR country IN ('', '(not set)')), 'Shown as (not set)' FROM e
UNION ALL SELECT 'data_deleted_source_rows', COUNTIF(first_user_source = '(data deleted)'), 'Obfuscation artefact; channel = Data deleted' FROM e
UNION ALL SELECT 'other_source_rows', COUNTIF(first_user_source = '<Other>'), 'Obfuscation artefact; channel = Other' FROM e
UNION ALL SELECT 'utc_date_differs_rows', COUNTIF(DATE(event_ts) != event_dt), 'event_date is property time zone, timestamp is UTC' FROM e
UNION ALL SELECT 'duplicate_extra_copies', CAST(extra_copies AS FLOAT64), 'Same user, microsecond, event and session; reported, not removed' FROM dup
UNION ALL SELECT 'purchase_events', COUNT(*), 'Rows with event_name = purchase' FROM p
UNION ALL SELECT 'purchase_null_or_not_set_transaction_id', COUNTIF(transaction_id IS NULL OR transaction_id = '(not set)'), 'Excluded from validated orders' FROM p
UNION ALL SELECT 'purchase_null_revenue', COUNTIF(purchase_revenue_usd IS NULL), 'Treated as 0 revenue' FROM p
UNION ALL SELECT 'validated_orders', COUNT(*), 'Distinct valid transaction_id' FROM per_tx
UNION ALL SELECT 'orders_with_repeat_purchase_events', COUNTIF(n > 1), 'Reason revenue is de-duplicated' FROM per_tx
UNION ALL SELECT 'revenue_summing_every_event_usd', ROUND(SUM(purchase_revenue_usd), 2), 'NOT used: may double count' FROM p
UNION ALL SELECT 'revenue_deduplicated_usd', ROUND(SUM(rev), 2), 'Used everywhere in this project' FROM per_tx;
