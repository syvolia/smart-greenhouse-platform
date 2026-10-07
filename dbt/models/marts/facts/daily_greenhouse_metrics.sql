{{ config(materialized='table') }}

SELECT
    z.greenhouse_id,
    DATE_TRUNC('day', f.reading_timestamp)::date AS metric_date,
    f.sensor_type,
    COUNT(*)                                     AS sample_count,
    AVG(f.reading_value)                         AS avg_value,
    MIN(f.reading_value)                         AS min_value,
    MAX(f.reading_value)                         AS max_value,
    STDDEV_POP(f.reading_value)                  AS std_value,
    SUM(CASE WHEN f.is_outlier THEN 1 ELSE 0 END) AS outlier_count
FROM {{ ref('fact_sensor_readings') }} f
JOIN {{ ref('dim_zone') }} z ON z.zone_id = f.zone_id
WHERE f.is_outlier = false
GROUP BY 1, 2, 3