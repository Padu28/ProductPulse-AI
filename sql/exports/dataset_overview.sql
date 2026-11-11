-- EXPORT: dataset_overview.csv | Grain: one row for the whole sample.
SELECT
  MIN(event_dt)                                   AS first_event_date,
  MAX(event_dt)                                   AS last_event_date,
  COUNT(DISTINCT event_dt)                        AS days_with_data,
  COUNT(*)                                        AS event_rows,
  COUNT(DISTINCT user_pseudo_id)                  AS identified_users,
  COUNTIF(user_pseudo_id IS NULL)                 AS null_user_id_rows,
  COUNTIF(ga_session_id IS NULL)                  AS null_session_id_rows,
  COUNT(DISTINCT IF(ga_session_id IS NOT NULL AND user_pseudo_id IS NOT NULL,
        CONCAT(user_pseudo_id, '-', CAST(ga_session_id AS STRING)), NULL)) AS sessions,
  COUNT(DISTINCT event_name)                      AS distinct_event_names
FROM `YOUR_PROJECT.productpulse.events_base`;
