"""Data quality gates on the raw and staging layers.

Fails the DAG when:
  - no readings have arrived in the last 15 minutes
  - duplicate (sensor_id, timestamp) rows exist in raw
  - sensor_id refers to a missing sensor
  - an impossible value slipped past cleaning
  - a large ingestion gap exists (no readings for > 1 hour)
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

from _common import DEFAULT_ARGS

POSTGRES_CONN_ID = "greenhouse_postgres"


def _run_sql(sql: str):
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


def check_recent_readings():
    rows = _run_sql("""
        SELECT COUNT(*) FROM public.sensor_readings
        WHERE "timestamp" >= now() - interval '15 minutes'
    """)
    if rows[0][0] == 0:
        raise ValueError("No readings in last 15 minutes.")


def check_duplicates():
    rows = _run_sql("""
        SELECT COUNT(*) FROM (
            SELECT sensor_id, "timestamp"
            FROM public.sensor_readings
            GROUP BY 1, 2 HAVING COUNT(*) > 1
        ) t
    """)
    if rows[0][0] > 0:
        raise ValueError(f"Found {rows[0][0]} duplicate (sensor_id, timestamp) pairs.")


def check_orphan_sensor_ids():
    rows = _run_sql("""
        SELECT COUNT(*) FROM public.sensor_readings r
        LEFT JOIN public.sensors s ON s.id = r.sensor_id
        WHERE s.id IS NULL
    """)
    if rows[0][0] > 0:
        raise ValueError(f"{rows[0][0]} readings reference missing sensors.")


def check_impossible_values():
    rows = _run_sql("""
        SELECT COUNT(*) FROM public.sensor_readings r
        JOIN public.sensors s ON s.id = r.sensor_id
        WHERE
            (s.sensor_type = 'temperature'   AND (r.value < -50 OR r.value > 80)) OR
            (s.sensor_type = 'humidity'      AND (r.value < 0   OR r.value > 100)) OR
            (s.sensor_type = 'soil_moisture' AND (r.value < 0   OR r.value > 100)) OR
            (s.sensor_type = 'co2'           AND (r.value < 0   OR r.value > 10000))
    """)
    if rows[0][0] > 0:
        raise ValueError(f"{rows[0][0]} impossible values in raw.")


def check_ingestion_gap():
    rows = _run_sql("""
        SELECT MAX("timestamp") FROM public.sensor_readings
    """)
    latest = rows[0][0]
    if latest is None:
        raise ValueError("No readings at all.")
    if latest < datetime.utcnow() - timedelta(hours=1):
        raise ValueError(f"Ingestion gap: latest reading is {latest}.")


with DAG(
    dag_id="data_quality_validation",
    description="Quality gates on raw + staging sensor data.",
    schedule="*/15 * * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["quality", "phase7"],
) as dag:

    t1 = PythonOperator(task_id="recent_readings", python_callable=check_recent_readings)
    t2 = PythonOperator(task_id="duplicates", python_callable=check_duplicates)
    t3 = PythonOperator(task_id="orphan_sensor_ids", python_callable=check_orphan_sensor_ids)
    t4 = PythonOperator(task_id="impossible_values", python_callable=check_impossible_values)
    t5 = PythonOperator(task_id="ingestion_gap", python_callable=check_ingestion_gap)

    t1 >> [t2, t3, t4, t5]