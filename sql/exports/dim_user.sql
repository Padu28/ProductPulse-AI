-- EXPORT: dim_user.csv | Grain: one row per user_pseudo_id (dimension table).
-- Device and country = values on the user's FIRST observed event.
-- Source / medium / channel are user-level first-touch fields in GA4.
-- Contains the obfuscated user_pseudo_id: keep this file local (git-ignored).
WITH ranked AS (
  SELECT
    user_pseudo_id,
    device_category,
    country,
    first_user_source,
    first_user_medium,
    channel_group,
    ROW_NUMBER() OVER (
      PARTITION BY user_pseudo_id
      ORDER BY event_timestamp, event_name) AS rn
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
),
span AS (
  SELECT
    user_pseudo_id,
    MIN(event_dt)                    AS first_seen_dt,
    MAX(event_dt)                    AS last_seen_dt,
    COUNT(DISTINCT device_category)  AS n_devices
  FROM `YOUR_PROJECT.productpulse.events_base`
  WHERE user_pseudo_id IS NOT NULL
  GROUP BY user_pseudo_id
)
SELECT
  r.user_pseudo_id,
  s.first_seen_dt,
  s.last_seen_dt,
  DATE_TRUNC(s.first_seen_dt, MONTH)                 AS cohort_month,
  IFNULL(r.device_category, '(not set)')             AS device_category,
  IFNULL(NULLIF(r.country, ''), '(not set)')         AS country,
  IFNULL(r.first_user_source, '(not set)')           AS first_user_source,
  IFNULL(r.first_user_medium, '(not set)')           AS first_user_medium,
  r.channel_group,
  s.n_devices
FROM ranked AS r
JOIN span AS s USING (user_pseudo_id)
WHERE r.rn = 1;
