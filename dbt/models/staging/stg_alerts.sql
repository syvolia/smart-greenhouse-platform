{{ config(materialized='view') }}

SELECT
    id::int                     AS alert_id,
    greenhouse_id::int          AS greenhouse_id,
    zone_id::int                AS zone_id,
    sensor_id::int              AS sensor_id,
    alert_type::text            AS alert_type,
    severity::text              AS severity,
    status::text                AS status,
    message::text               AS message,
    value::numeric(12,4)        AS value,
    threshold::text             AS threshold,
    created_at::timestamptz,
    acknowledged_at::timestamptz,
    resolved_at::timestamptz
FROM {{ source('operational', 'alerts') }}