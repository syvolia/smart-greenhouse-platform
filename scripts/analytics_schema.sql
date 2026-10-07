-- Raw: read-only view over the operational table. Pipeline treats this as
-- the canonical "as-landed" source.
CREATE SCHEMA IF NOT EXISTS raw;

CREATE OR REPLACE VIEW raw.sensor_readings AS
SELECT id, sensor_id, "timestamp", value
FROM public.sensor_readings;

CREATE OR REPLACE VIEW raw.greenhouses AS
SELECT id, name, location, status, created_at, updated_at
FROM public.greenhouses;

CREATE OR REPLACE VIEW raw.zones AS
SELECT * FROM public.zones;

CREATE OR REPLACE VIEW raw.sensors AS
SELECT * FROM public.sensors;

CREATE OR REPLACE VIEW raw.alerts AS
SELECT * FROM public.alerts;

-- Staging: Spark writes cleaned/aggregated data here.
CREATE SCHEMA IF NOT EXISTS staging;

-- Analytics: dbt owns everything in this schema.
CREATE SCHEMA IF NOT EXISTS analytics;

-- Airflow metadata db
-- (Run separately if the DB doesn't exist:
--   CREATE DATABASE airflow;)