import os, logging
import boto3, requests
from botocore.config import Config
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

# Config
DATE = os.environ.get("INGEST_DATE", "2025-01-15")
ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
BRONZE = "bronze"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("downloader")

# Connect to MinIO
s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=os.environ["MINIO_ROOT_USER"],
    aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    config=Config(s3={"addressing_style": "path"}),
)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(log, logging.WARNING),
)
def download(url):
    """Fetch a file over HTTPS; retried with backoff on any failure."""
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content

def already_ingested(key):
    """True if the object is already in bronze (idempotency check)."""
    try:
        s3.head_object(Bucket=BRONZE, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise

def ingest_hour(date, hour):
    key = f"{date}-{hour}.json.gz"
    if already_ingested(key):
        log.info("skip  %s (already in bronze)", key)
        return
    url = f"https://data.gharchive.org/{date}-{hour}.json.gz"
    data = download(url)
    s3.put_object(Bucket=BRONZE, Key=key, Body=data)
    log.info("store %s (%d bytes)", key, len(data))

def main():
    log.info("ingesting %s", DATE)
    for hour in range(24):
        ingest_hour(DATE, hour)
    log.info("done %s", DATE)

if __name__ == "__main__":
    main()