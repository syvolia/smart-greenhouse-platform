{{ config(materialized='view') }}

SELECT
    id::int               AS greenhouse_id,
    name::text            AS greenhouse_name,
    location::text        AS location,
    status::text          AS status,
    created_at::timestamptz,
    updated_at::timestamptz
FROM {{ source('operational', 'greenhouses') }}