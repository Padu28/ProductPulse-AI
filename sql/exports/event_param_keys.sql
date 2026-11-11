-- EXPORT: event_param_keys.csv | Grain: one row per event_params key.
-- Intentional unnest: occurrences counts parameters, not events.
SELECT
  ep.key,
  COUNT(*)                                   AS occurrences,
  COUNTIF(ep.value.string_value IS NOT NULL) AS string_values,
  COUNTIF(ep.value.int_value    IS NOT NULL) AS int_values,
  COUNTIF(ep.value.float_value  IS NOT NULL) AS float_values,
  COUNTIF(ep.value.double_value IS NOT NULL) AS double_values
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
     UNNEST(event_params) AS ep
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY ep.key
ORDER BY occurrences DESC;
