"""Shared Airflow config: connection, default args, spark paths."""
import os
from datetime import datetime, timedelta

from airflow.models import Connection

SPARK_MASTER_URL = os.environ.get("SPARK_MASTER_URL", "spark://spark-master:7077")
SPARK_JOBS_DIR = "/opt/spark/jobs"
DBT_PROJECT_DIR = "/opt/dbt"
DBT_PROFILES_DIR = "/opt/dbt"

# Env vars Airflow hands to Spark and dbt subprocesses.
PG_ENV = {
    "POSTGRES_HOST": os.environ["POSTGRES_HOST"],
    "POSTGRES_PORT": os.environ["POSTGRES_PORT"],
    "POSTGRES_DB": os.environ["POSTGRES_DB"],
    "POSTGRES_USER": os.environ["POSTGRES_USER"],
    "POSTGRES_PASSWORD": os.environ["POSTGRES_PASSWORD"],
}

DEFAULT_ARGS = {
    "owner": "data-eng",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "start_date": datetime(2026, 1, 1),
}