"""Daily roll-up: build daily metrics + publish sensor health summary."""
from airflow import DAG
from airflow.operators.bash import BashOperator

from _common import DBT_PROFILES_DIR, DBT_PROJECT_DIR, DEFAULT_ARGS, PG_ENV

DBT_BIN = "/home/airflow/dbt-venv/bin/dbt"

with DAG(
    dag_id="daily_greenhouse_analytics",
    description="Daily marts and health summaries for greenhouse dashboards.",
    schedule="0 2 * * *",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["analytics", "phase7"],
) as dag:

    build_marts = BashOperator(
        task_id="dbt_build_analytics_marts",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"{DBT_BIN} run "
            f"--select marts "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR}"
        ),
        env=PG_ENV,
        append_env=True,
    )

    test_marts = BashOperator(
        task_id="dbt_test_analytics_marts",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"{DBT_BIN} test "
            f"--select marts "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR}"
        ),
        env=PG_ENV,
        append_env=True,
    )

    build_marts >> test_marts