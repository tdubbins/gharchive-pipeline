import os, boto3, requests
from botocore.config import Config

URL = "https://data.gharchive.org/2025-01-15-12.json.gz"
KEY = "2025-01-15-12.json.gz"

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id=os.environ["MINIO_ROOT_USER"],
    aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    config=Config(s3={"addressing_style": "path"}),
)

response = requests.get(URL)
response.raise_for_status()
data = response.content

s3.put_object(Bucket="bronze", Key=KEY, Body=data)
print(f"uploaded {len(data)} bytes to bronze/{KEY}")