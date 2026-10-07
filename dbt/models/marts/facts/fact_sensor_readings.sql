{{ config(materialized='table') }}

SELECT
    r.reading_id,
    r.reading_timestamp,
    DATE_TRUNC('hour', r.reading_timestamp) AS hour_utc,
    r.sensor_id,
    s.zone_id,
    z.greenhouse_id,
    r.sensor_type,
    r.reading_value,
    r.is_outlier
FROM {{ ref('stg_sensor_readings') }} r
JOIN {{ ref('stg_sensors') }} s ON s.sensor_id = r.sensor_id
JOIN {{ ref('stg_zones') }} z ON z.zone_id = s.zone_id