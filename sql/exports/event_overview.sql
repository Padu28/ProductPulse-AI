-- EXPORT: event_overview.csv | Grain: one row per event_name.
SELECT
  event_name,
  COUNT(*)                        AS event_rows,
  COUNT(DISTINCT user_pseudo_id)  AS users
FROM `YOUR_PROJECT.productpulse.events_base`
GROUP BY event_name
ORDER BY event_rows DESC;
