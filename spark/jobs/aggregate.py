import os
from pyspark.sql import SparkSession, functions as F

DATE = os.environ.get("INGEST_DATE", "2025-01-15")

spark = (
    SparkSession.builder
    .appName("silver-to-gold")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", os.environ["MINIO_ROOT_USER"])
    .config("spark.hadoop.fs.s3a.secret.key", os.environ["MINIO_ROOT_PASSWORD"])
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    .getOrCreate()
)

# Read this day's silver
silver = spark.read.parquet("s3a://silver/").filter(F.col("date") == DATE)

# Aggregate to hour_ts x event_type x is_bot -> count
gold = (
    silver
    .withColumn("hour_ts", F.date_trunc("hour", "created_at"))
    .groupBy("hour_ts", "event_type", "is_bot")
    .count()
    .withColumnRenamed("count", "event_count")
    .withColumn("date", F.to_date("hour_ts"))
)

# Write gold as date-partitioned Parquet
(gold.write
    .mode("overwrite")
    .partitionBy("date")
    .parquet("s3a://gold/"))

print(f"gold written for {DATE}: {gold.count()} rows")
spark.stop()