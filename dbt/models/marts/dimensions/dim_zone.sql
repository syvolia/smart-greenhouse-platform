{{ config(materialized='table') }}

SELECT
    zone_id,
    greenhouse_id,
    zone_name,
    crop_type,
    target_temperature_min,
    target_temperature_max,
    target_humidity_min,
    target_humidity_max,
    target_soil_moisture_min,
    target_soil_moisture_max
FROM {{ ref('stg_zones') }}