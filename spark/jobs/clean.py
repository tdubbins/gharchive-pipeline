import os
from pyspark.sql import functions as F
from session import get_spark

DATE = os.environ.get("INGEST_DATE", "2025-01-15")
spark = get_spark("bronze-to-silver")

# Read all 24 hourly files for specified day
raw = spark.read.json(f"s3a://bronze/{DATE}-*.json.gz")

# Flatten, clean, derive
silver = raw.select(
    F.col("id"),
    F.to_timestamp("created_at").alias("created_at"),
    F.col("type").alias("event_type"),
    F.col("actor.login").alias("actor_login"),
    F.col("actor.id").alias("actor_id"),
    F.col("repo.name").alias("repo_name"),
    F.coalesce(F.col("actor.login").endswith("[bot]"), F.lit(False)).alias("is_bot"),
    F.to_date("created_at").alias("date"),
)

# Write to silver as date-partitioned Parquet
(silver.write
    .mode("overwrite")
    .partitionBy("date")
    .parquet("s3a://silver/"))

print(f"silver written for {DATE}: {silver.count()} rows")
spark.stop()