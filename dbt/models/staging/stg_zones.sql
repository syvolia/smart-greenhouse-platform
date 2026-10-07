{{ config(materialized='view') }}

SELECT
    id::int                        AS zone_id,
    greenhouse_id::int             AS greenhouse_id,
    name::text                     AS zone_name,
    crop_type::text                AS crop_type,
    target_temperature_min::numeric(6,2)  AS target_temperature_min,
    target_temperature_max::numeric(6,2)  AS target_temperature_max,
    target_humidity_min::numeric(5,2)     AS target_humidity_min,
    target_humidity_max::numeric(5,2)     AS target_humidity_max,
    target_soil_moisture_min::numeric(5,2) AS target_soil_moisture_min,
    target_soil_moisture_max::numeric(5,2) AS target_soil_moisture_max
FROM {{ source('operational', 'zones') }}