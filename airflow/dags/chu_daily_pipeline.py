"""
DAG principal CHU - Orchestration du pipeline quotidien.

Ce DAG orchestre:
1. Extract: recuperation des donnees PostgreSQL et CSV
2. Load: chargement du staging bronze
3. Transform: alimentation du modele gold
4. Validate: controle qualite des tables gold
5. Notify: log de fin de pipeline

Schedule: Quotidien a minuit (0 0 * * *)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# utils.py est dans /opt/airflow/dags, déjà sur le PYTHONPATH Airflow
from utils import run_python_script, run_sql_on_postgres, log_step

default_args = {
    "owner": "chu_team",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2025, 1, 1),
}

with DAG(
    "chu_daily_pipeline",
    default_args=default_args,
    description="Pipeline quotidien CHU: Extract, Load, Transform, Validate",
    schedule_interval="0 0 * * *",
    catchup=False,
    tags=["chu", "production"],
) as dag:

    # EXTRACT

    extract_postgres = PythonOperator(
        task_id="extract_postgres",
        python_callable=run_python_script,
        op_kwargs={"script": "extract/extract_postgres.py"},
        doc_md="Extraction PostgreSQL (consultations, patients, hospit.) vers Bronze",
    )

    extract_csv = PythonOperator(
        task_id="extract_csv",
        python_callable=run_python_script,
        op_kwargs={"script": "extract/extract_csv.py"},
        doc_md="Extraction CSV sources (etablissements, deces, satisfaction) vers Bronze",
    )

    # Perspective seulement si une source FTP existe un jour.
    # extract_ftp = PythonOperator(
    #     task_id="extract_ftp",
    #     python_callable=run_python_script,
    #     op_kwargs={"script": "extract/extract_ftp.py"},
    #     doc_md="Extraction FTP optionnelle vers raw (activee par variables d'environnement)",
    # )

    # LOAD

    load_staging_consultations = PythonOperator(
        task_id="load_staging_consultations",
        python_callable=run_python_script,
        op_kwargs={"script": "load/load_to_warehouse.py"},
        doc_md="Chargement du staging consultations depuis Bronze vers PostgreSQL",
    )

    # TRANSFORM

    transform_consultations = PythonOperator(
        task_id="transform_consultations",
        python_callable=run_sql_on_postgres,
        op_kwargs={
            "sql_file": "transform/transform_consultations.sql",
            "schema": "gold",
        },
        doc_md="Transformation et alimentation des dimensions et faits Gold",
    )

    # VALIDATE

    validate_gold = PythonOperator(
        task_id="validate_gold",
        python_callable=run_python_script,
        op_kwargs={"script": "validate_gold.py"},
        doc_md="Contrôles qualité Gold: nulls, doublons, seuils lignes",
    )

    # NOTIFY

    notify_success = PythonOperator(
        task_id="notify_success",
        python_callable=lambda **ctx: log_step("pipeline", "success"),
        trigger_rule="all_success",
        doc_md="Log de fin de pipeline (optionnel: brancher sur Slack/email)",
    )

    # DEPENDENCIES

    [extract_postgres, extract_csv] >> load_staging_consultations
    load_staging_consultations >> transform_consultations >> validate_gold >> notify_success
