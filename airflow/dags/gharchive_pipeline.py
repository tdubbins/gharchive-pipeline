"""Full batch pipeline: download -> clean -> aggregate -> load."""
import os
import datetime

from airflow.sdk import DAG
from airflow.providers.docker.operators.docker import DockerOperator

NETWORK = "gharchive-pipeline_default"

MINIO_ENV = {
    "MINIO_ENDPOINT": "http://minio:9000",
    "MINIO_ROOT_USER": os.environ["MINIO_ROOT_USER"],
    "MINIO_ROOT_PASSWORD": os.environ["MINIO_ROOT_PASSWORD"],
}
POSTGRES_ENV = {
    "POSTGRES_USER": os.environ["POSTGRES_USER"],
    "POSTGRES_PASSWORD": os.environ["POSTGRES_PASSWORD"],
    "POSTGRES_DB": os.environ["POSTGRES_DB"],
}

def spark_task(task_id, job):
    """One Spark job, run as the driver in an ephemeral container against the cluster."""
    return DockerOperator(
        task_id=task_id,
        image="gharchive-spark:4.1.2",
        command=(
            "/opt/spark/bin/spark-submit "
            "--master spark://spark-master:7077 "
            f"/opt/spark/jobs/{job}"
        ),
        environment={**MINIO_ENV, **POSTGRES_ENV},
        network_mode=NETWORK,
        auto_remove="success",
        mount_tmp_dir=False,
    )

with DAG(
    dag_id="gharchive_pipeline",
    start_date=datetime.datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["gharchive"],
) as dag:
    download = DockerOperator(
        task_id="download",
        image="gharchive-downloader:1.0",
        environment=MINIO_ENV,
        network_mode=NETWORK,
        auto_remove="success",
        mount_tmp_dir=False,
    )
    clean = spark_task("clean", "clean.py")
    aggregate = spark_task("aggregate", "aggregate.py")
    load = spark_task("load", "load.py")

    download >> clean >> aggregate >> load