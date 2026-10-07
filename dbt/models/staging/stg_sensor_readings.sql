{{ config(materialized='view') }}

SELECT
    id::bigint            AS reading_id,
    sensor_id::int        AS sensor_id,
    sensor_type::text     AS sensor_type,
    "timestamp"::timestamptz AS reading_timestamp,
    value::numeric(12,4)  AS reading_value,
    is_outlier::boolean   AS is_outlier
FROM {{ source('spark_staging', 'sensor_readings_clean') }}