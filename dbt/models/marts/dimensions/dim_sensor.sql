{{ config(materialized='table') }}

SELECT
    sensor_id,
    zone_id,
    sensor_type,
    unit,
    status,
    created_at
FROM {{ ref('stg_sensors') }}