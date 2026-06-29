import os
from session import get_spark

DATE = os.environ.get("INGEST_DATE", "2025-01-15")
spark = get_spark("gold-to-postgres")

# Build JDBC connection details from env
url  = f"jdbc:postgresql://postgres:5432/{os.environ['POSTGRES_DB']}"
user = os.environ["POSTGRES_USER"]
pw   = os.environ["POSTGRES_PASSWORD"]

# Read this day's gold
gold = spark.read.parquet("s3a://gold/").filter(f"date = '{DATE}'")

# Delete this day's rows first to avoid duplicates
conn = spark._jvm.java.sql.DriverManager.getConnection(url, user, pw)
stmt = conn.prepareStatement("DELETE FROM fact_event_counts WHERE date = ?::date")
stmt.setString(1, DATE)
deleted = stmt.executeUpdate()
stmt.close()
conn.close()
print(f"deleted {deleted} existing rows for {DATE}")

# Append this day's gold
(gold.write
    .format("jdbc")
    .option("url", url)
    .option("dbtable", "fact_event_counts")
    .option("user", user)
    .option("password", pw)
    .option("driver", "org.postgresql.Driver")
    .mode("append")
    .save())

print(f"loaded gold for {DATE}: {gold.count()} rows")
spark.stop()