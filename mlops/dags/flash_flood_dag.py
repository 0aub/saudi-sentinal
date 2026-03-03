# Implementation guide: see docs/plans/LEVEL-2-MLOPS.md — "Airflow DAGs" section
"""
Airflow DAG for the flash-flood project.

Schedule: Annual risk update
Cron: 0 6 1 1 *
AOIs: jeddah-wadis

Pipeline steps (per docs/plans/LEVEL-2-MLOPS.md):
  1. check_new_tiles   — Query Level 0 Tile API for new chips since last run
  2. preprocess_tiles  — Apply project-specific preprocessing
  3. run_inference     — Load Production model from MLflow, run inference on new chips
  4. validate_output   — Check prediction quality against thresholds
  5. store_results     — Write predictions to PostGIS + MinIO
  6. send_alerts       — Evaluate alert rules, push to alerting system

See: docs/plans/LEVEL-2-MLOPS.md — "DAG Schedule Summary"
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

PROJECT = "flash-flood"
MODEL_NAME = "flash-flood-model"

default_args = {
    "owner": "saudi-sentinel-ai",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}


def check_new_tiles(**ctx):
    raise NotImplementedError("Query Tile API: GET /api/v1/aois/{aoi}/chips?start=<last_run>")

def preprocess_tiles(**ctx):
    raise NotImplementedError(f"Project-specific preprocessing for {PROJECT}")

def run_inference(**ctx):
    raise NotImplementedError("Load ONNX from MLflow registry, batch inference on chips")

def validate_predictions(**ctx):
    raise NotImplementedError("Check confidence distribution, area thresholds")

def store_results(**ctx):
    raise NotImplementedError("Write rasters to MinIO, metadata to PostGIS predictions table")

def check_and_alert(**ctx):
    raise NotImplementedError("Evaluate ALERT_RULES from system/alerts/rules.py")


with DAG(
    "flash_flood_pipeline",
    default_args=default_args,
    schedule_interval="0 6 1 1 *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["saudi-sentinel", "flash-flood"],
) as dag:
    t1 = PythonOperator(task_id="check_new_tiles",    python_callable=check_new_tiles)
    t2 = PythonOperator(task_id="preprocess_tiles",   python_callable=preprocess_tiles)
    t3 = PythonOperator(task_id="run_inference",      python_callable=run_inference)
    t4 = PythonOperator(task_id="validate_output",    python_callable=validate_predictions)
    t5 = PythonOperator(task_id="store_results",      python_callable=store_results)
    t6 = PythonOperator(task_id="send_alerts",        python_callable=check_and_alert)

    t1 >> t2 >> t3 >> t4 >> t5 >> t6
