# Stage 1: Get Spark binaries from the official image
FROM apache/spark:3.5.1-python3 AS spark-dist

# Stage 2: Build the Airflow image
FROM apache/airflow:2.9.2-python3.11

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy Spark from the first stage
COPY --from=spark-dist /opt/spark /opt/spark

# Download PostgreSQL JDBC driver with retries for network resilience
RUN curl -fL --retry 5 --retry-delay 5 --retry-all-errors \
    -o /opt/spark/jars/postgresql-42.7.3.jar \
    https://jdbc.postgresql.org/download/postgresql-42.7.3.jar

# Set Spark and Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV SPARK_HOME=/opt/spark
ENV PATH="${SPARK_HOME}/bin:${PATH}"
ENV PYSPARK_PYTHON=python3

USER airflow

# 1. Install Airflow providers using the constraints file.
#    This lets Airflow's resolver pick compatible versions.
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.2/constraints-3.11.txt" \
    -r /requirements.txt

# 2. Create an isolated virtual environment for dbt.
RUN python -m venv /home/airflow/dbt-venv

# 3. Install dbt into the virtual environment.
#    This completely isolates it from Airflow's dependencies.
RUN /home/airflow/dbt-venv/bin/pip install --no-cache-dir "dbt-postgres==1.8.2"

# Ensure dbt is accessible via absolute path
ENV DBT_VENV_PATH=/home/airflow/dbt-venv