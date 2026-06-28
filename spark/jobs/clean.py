import os
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("s3a-read-test")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", os.environ["MINIO_ROOT_USER"])
    .config("spark.hadoop.fs.s3a.secret.key", os.environ["MINIO_ROOT_PASSWORD"])
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .getOrCreate()
)

df = spark.read.json("s3a://bronze/2025-01-15-12.json.gz")
print("ROW COUNT:", df.count())
df.printSchema()
df.show(3, truncate=True)
spark.stop()