{{ config(materialized='table') }}

SELECT
    h.zone_id,
    z.greenhouse_id,
    h.sensor_type,
    h.hour_utc,
    h.min_value,
    h.max_value,
    h.avg_value,
    h.std_value,
    h.sample_count
FROM {{ source('spark_staging', 'hourly_zone_metrics') }} h
JOIN {{ ref('dim_zone') }} z ON z.zone_id = h.zone_id