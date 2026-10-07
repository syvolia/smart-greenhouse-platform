{{ config(materialized='view') }}

SELECT
    id::int             AS sensor_id,
    zone_id::int        AS zone_id,
    sensor_type::text   AS sensor_type,
    unit::text          AS unit,
    status::text        AS status,
    created_at::timestamptz
FROM {{ source('operational', 'sensors') }}