{{ config(materialized='table') }}

SELECT
    greenhouse_id,
    greenhouse_name,
    location,
    status,
    created_at,
    updated_at
FROM {{ ref('stg_greenhouses') }}