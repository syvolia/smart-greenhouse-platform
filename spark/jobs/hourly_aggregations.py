"""Aggregate staging.sensor_readings_clean into staging.hourly_zone_metrics.

Grain: (zone_id, sensor_type, hour_utc)
Metrics: min, max, avg, count, stddev, outlier_count
"""
import os
import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

PG_HOST = os.environ.get("POSTGRES_HOST", "postgres")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_DB = os.environ["POSTGRES_DB"]
PG_USER = os.environ["POSTGRES_USER"]
PG_PASS = os.environ["POSTGRES_PASSWORD"]

JDBC_URL = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"
JDBC_PROPS = {"user": PG_USER, "password": PG_PASS, "driver": "org.postgresql.Driver"}


def main() -> None:
    spark = SparkSession.builder.appName("hourly_aggregations").getOrCreate()

    clean = spark.read.jdbc(JDBC_URL, "staging.sensor_readings_clean", properties=JDBC_PROPS)
    sensors = spark.read.jdbc(JDBC_URL, "raw.sensors", properties=JDBC_PROPS)

    joined = clean.join(
        sensors.select(F.col("id").alias("sensor_id"), F.col("zone_id")),
        on="sensor_id",
        how="inner",
    )

    hourly = (
        joined
        .filter(F.col("is_outlier") == False)  # noqa: E712
        .withColumn("hour_utc", F.date_trunc("hour", F.col("timestamp")))
        .groupBy("zone_id", "sensor_type", "hour_utc")
        .agg(
            F.min("value").alias("min_value"),
            F.max("value").alias("max_value"),
            F.avg("value").alias("avg_value"),
            F.stddev_pop("value").alias("std_value"),
            F.count("*").alias("sample_count"),
        )
    )

    out = hourly.select(
        F.col("zone_id").cast("int"),
        F.col("sensor_type").cast("string"),
        F.col("hour_utc").cast("timestamp"),
        F.col("min_value").cast("double"),
        F.col("max_value").cast("double"),
        F.col("avg_value").cast("double"),
        F.col("std_value").cast("double"),
        F.col("sample_count").cast("long"),
    )

    out.write \
        .mode("overwrite") \
        .option("truncate", "true") \
        .jdbc(JDBC_URL, "staging.hourly_zone_metrics", properties=JDBC_PROPS)

    print(f"hourly_aggregations: wrote {out.count()} rows", file=sys.stderr)
    spark.stop()


if __name__ == "__main__":
    main()