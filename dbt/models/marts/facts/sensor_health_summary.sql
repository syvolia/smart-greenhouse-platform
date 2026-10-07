{{ config(materialized='table') }}

WITH base AS (
    SELECT
        sensor_id,
        zone_id,
        greenhouse_id,
        sensor_type,
        COUNT(*)                                    AS total_readings,
        SUM(CASE WHEN is_outlier THEN 1 ELSE 0 END) AS outlier_readings,
        MAX(reading_timestamp)                      AS last_seen_at
    FROM {{ ref('fact_sensor_readings') }}
    GROUP BY 1, 2, 3, 4
)
SELECT
    sensor_id,
    zone_id,
    greenhouse_id,
    sensor_type,
    total_readings,
    outlier_readings,
    ROUND(
        outlier_readings::numeric / NULLIF(total_readings, 0) * 100, 2
    )                                               AS outlier_pct,
    last_seen_at,
    (now() - last_seen_at) < interval '5 minutes'  AS is_reporting
FROM base