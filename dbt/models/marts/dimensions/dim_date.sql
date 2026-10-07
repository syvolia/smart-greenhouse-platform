{{ config(materialized='table') }}

WITH bounds AS (
    SELECT
        MIN(reading_timestamp)::date AS min_date,
        MAX(reading_timestamp)::date AS max_date
    FROM {{ ref('stg_sensor_readings') }}
)
SELECT
    d::date                        AS date_day,
    EXTRACT(YEAR  FROM d)::int     AS year,
    EXTRACT(MONTH FROM d)::int     AS month,
    EXTRACT(DAY   FROM d)::int     AS day,
    EXTRACT(DOW   FROM d)::int     AS day_of_week,
    EXTRACT(WEEK  FROM d)::int     AS week_of_year
FROM bounds,
     generate_series(min_date, max_date, '1 day'::interval) AS d