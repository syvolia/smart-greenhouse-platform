"""Clean raw sensor readings and write to staging.sensor_readings_clean.

Steps:
  1. Read raw.sensor_readings via JDBC.
  2. Drop rows with NULL sensor_id / timestamp / value.
  3. Normalize timestamps to UTC.
  4. Drop duplicates on (sensor_id, timestamp), keeping the latest insert id.
  5. Filter physically impossible values.
  6. Flag statistical outliers per sensor via rolling z-score.
  7. Overwrite staging.sensor_readings_clean.
"""
import os
import sys

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

PG_HOST = os.environ.get("POSTGRES_HOST", "postgres")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_DB = os.environ["POSTGRES_DB"]
PG_USER = os.environ["POSTGRES_USER"]
PG_PASS = os.environ["POSTGRES_PASSWORD"]

JDBC_URL = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"
JDBC_PROPS = {"user": PG_USER, "password": PG_PASS, "driver": "org.postgresql.Driver"}

# Physically impossible bounds per sensor type.
# Values outside these are dropped before outlier flagging.
IMPOSSIBLE_BOUNDS = {
    "temperature": (-50.0, 80.0),
    "humidity": (0.0, 100.0),
    "soil_moisture": (0.0, 100.0),
    "light": (0.0, 200_000.0),
    "co2": (0.0, 10_000.0),
    "irrigation": (0.0, 1000.0),
}

ZSCORE_THRESHOLD = 5.0


def main() -> None:
    spark = (
        SparkSession.builder
        .appName("clean_sensor_readings")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    raw = spark.read.jdbc(JDBC_URL, "raw.sensor_readings", properties=JDBC_PROPS)

    # Basic hygiene
    cleaned = (
        raw
        .filter(F.col("sensor_id").isNotNull())
        .filter(F.col("timestamp").isNotNull())
        .filter(F.col("value").isNotNull())
        .withColumn("timestamp", F.to_utc_timestamp(F.col("timestamp"), "UTC"))
        .withColumn("value", F.col("value").cast("double"))
    )

    # Attach sensor_type for bounds + windowing
    sensors = spark.read.jdbc(JDBC_URL, "raw.sensors", properties=JDBC_PROPS) \
        .select(F.col("id").alias("sensor_id"), F.col("sensor_type"))

    joined = cleaned.join(sensors, on="sensor_id", how="inner")

    bounds = F.create_map(*[
        x for k, (lo, hi) in IMPOSSIBLE_BOUNDS.items()
        for x in (F.lit(k), F.struct(F.lit(lo).alias("lo"), F.lit(hi).alias("hi")))
    ])
    joined = joined.withColumn("bounds", bounds[F.col("sensor_type")])
    joined = joined.filter(
        (F.col("value") >= F.col("bounds.lo")) & (F.col("value") <= F.col("bounds.hi"))
    ).drop("bounds")

    # Deduplicate: keep newest id per (sensor_id, timestamp)
    dedup = (
        joined
        .withColumn(
            "rn",
            F.row_number().over(
                Window.partitionBy("sensor_id", "timestamp").orderBy(F.col("id").desc())
            ),
        )
        .filter(F.col("rn") == 1)
        .drop("rn")
    )

    # Rolling z-score for outlier flagging per sensor
    w = Window.partitionBy("sensor_id").orderBy("timestamp").rowsBetween(-59, -1)
    stats = dedup.withColumn("mean_60", F.avg("value").over(w)) \
                 .withColumn("std_60", F.stddev_pop("value").over(w))
    flagged = stats.withColumn(
        "is_outlier",
        F.when(
            (F.col("std_60") > 0) &
            (F.abs((F.col("value") - F.col("mean_60")) / F.col("std_60")) > ZSCORE_THRESHOLD),
            F.lit(True),
        ).otherwise(F.lit(False)),
    ).drop("mean_60", "std_60")

    out = flagged.select(
        F.col("id").cast("long").alias("id"),
        F.col("sensor_id").cast("int").alias("sensor_id"),
        F.col("sensor_type").cast("string").alias("sensor_type"),
        F.col("timestamp").cast("timestamp").alias("timestamp"),
        F.col("value").cast("double").alias("value"),
        F.col("is_outlier").cast("boolean").alias("is_outlier"),
    )

    # Truncate-then-append (idempotent)
    spark._jvm.org.postgresql.Driver  # noqa: B018  touch classpath
    out.write \
        .mode("overwrite") \
        .option("truncate", "true") \
        .jdbc(JDBC_URL, "staging.sensor_readings_clean", properties=JDBC_PROPS)

    print(f"clean_sensor_readings: wrote {out.count()} rows", file=sys.stderr)
    spark.stop()


if __name__ == "__main__":
    main()