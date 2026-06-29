import os
from pyspark.sql import functions as F
from session import get_spark

DATE = os.environ.get("INGEST_DATE", "2025-01-15")
spark = get_spark("silver-to-gold")

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