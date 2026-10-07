"""Sensor pipeline: Spark clean -> Spark aggregate -> dbt run -> dbt test."""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

from _common import (
    DBT_PROFILES_DIR,
    DBT_PROJECT_DIR,
    DEFAULT_ARGS,
    PG_ENV,
    SPARK_JOBS_DIR,
    SPARK_MASTER_URL,
)

# Absolute path to dbt inside the isolated virtualenv
DBT_BIN = "/home/airflow/dbt-venv/bin/dbt"

with DAG(
    dag_id="sensor_data_processing",
    description="Spark clean + aggregate + dbt transform over sensor readings.",
    schedule="*/15 * * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["pipeline", "phase7"],
) as dag:

    clean = SparkSubmitOperator(
        task_id="spark_clean_sensor_readings",
        application=f"{SPARK_JOBS_DIR}/clean_sensor_readings.py",
        conn_id="spark_default",
        name="clean_sensor_readings",
        conf={"spark.master": SPARK_MASTER_URL},
        env_vars=PG_ENV,
        verbose=False,
        deploy_mode="client",
    )

    aggregate = SparkSubmitOperator(
        task_id="spark_hourly_aggregations",
        application=f"{SPARK_JOBS_DIR}/hourly_aggregations.py",
        conn_id="spark_default",
        name="hourly_aggregations",
        conf={"spark.master": SPARK_MASTER_URL},
        env_vars=PG_ENV,
        verbose=False,
        deploy_mode="client",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"{DBT_BIN} run "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR}"
        ),
        env=PG_ENV,
        append_env=True,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"{DBT_BIN} test "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR}"
        ),
        env=PG_ENV,
        append_env=True,
    )

    clean >> aggregate >> dbt_run >> dbt_test