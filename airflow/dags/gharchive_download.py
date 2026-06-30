"""Launch the gharchive-downloader image as a one-off task (D18 de-risk slice)."""
import os
import datetime

from airflow.sdk import DAG
from airflow.providers.docker.operators.docker import DockerOperator

with DAG(
    dag_id="gharchive_download",
    start_date=datetime.datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["gharchive"],
) as dag:
    download = DockerOperator(
        task_id="download",
        image="gharchive-downloader:1.0",
        environment={
            "MINIO_ENDPOINT": "http://minio:9000",
            "MINIO_ROOT_USER": os.environ["MINIO_ROOT_USER"],
            "MINIO_ROOT_PASSWORD": os.environ["MINIO_ROOT_PASSWORD"],
        },
        network_mode="gharchive-pipeline_default",
        auto_remove="success",
        mount_tmp_dir=False,
    )