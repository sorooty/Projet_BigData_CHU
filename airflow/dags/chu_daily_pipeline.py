"""
DAG principal CHU - Orchestration pipeline quotidien

Ce DAG orchestre:
1. Extract: récupération des données PostgreSQL et CSV
2. Transform: transformations SQL (dimensions, faits) vers Gold
3. Validate: validation qualité données Gold
4. Notify: log de fin de pipeline

Schedule: Quotidien à minuit (0 0 * * *)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# utils.py est dans /opt/airflow/dags, déjà sur le PYTHONPATH Airflow
from utils import run_python_script, run_sql_on_postgres, log_step, validate_table

default_args = {
    "owner": "chu_team",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2025, 1, 1),
}

with DAG(
    "chu_daily_pipeline",
    default_args=default_args,
    description="Pipeline quotidien CHU: Extract → Transform → Load → Validate",
    schedule_interval="0 0 * * *",
    catchup=False,
    tags=["chu", "production"],
) as dag:

    # ── EXTRACT (parallèle) ──────────────────────────────────────────────────

    extract_postgres = PythonOperator(
        task_id="extract_postgres",
        python_callable=run_python_script,
        op_kwargs={"script": "extract/extract_postgres.py"},
        doc_md="Extraction PostgreSQL (consultations, patients, hospit.) → Parquet Bronze",
    )

    extract_csv = PythonOperator(
        task_id="extract_csv",
        python_callable=run_python_script,
        op_kwargs={"script": "extract/extract_csv.py"},
        doc_md="Extraction CSV sources (établissements, décès, satisfaction) → Parquet Bronze",
    )

    # ── TRANSFORM (séquentiel, ajouté au fur et à mesure) ───────────────────
    # Seyni ajoute ici les tâches quand les scripts collègues sont intégrés.
    # Exemple: transform_dimensions, transform_faits, etc.

    transform_placeholder = PythonOperator(
        task_id="transform_placeholder",
        python_callable=lambda **ctx: log_step("transform", "placeholder"),
        doc_md="Placeholder — remplacé par les vraies tâches transform en Phase 3",
    )

    # ── LOAD ─────────────────────────────────────────────────────────────────

    load_warehouse = PythonOperator(
        task_id="load_warehouse",
        python_callable=run_python_script,
        op_kwargs={"script": "load/load_to_warehouse.py"},
        doc_md="Chargement final dans Gold (schema gold PostgreSQL)",
    )

    # ── VALIDATE ─────────────────────────────────────────────────────────────

    validate_gold = PythonOperator(
        task_id="validate_gold",
        python_callable=run_python_script,
        op_kwargs={"script": "validate_gold.py"},
        doc_md="Contrôles qualité Gold: nulls, doublons, seuils lignes",
    )

    # ── NOTIFY ───────────────────────────────────────────────────────────────

    notify_success = PythonOperator(
        task_id="notify_success",
        python_callable=lambda **ctx: log_step("pipeline", "success"),
        trigger_rule="all_success",
        doc_md="Log de fin de pipeline (optionnel: brancher sur Slack/email)",
    )

    # ── DÉPENDANCES ──────────────────────────────────────────────────────────

    [extract_postgres, extract_csv] >> transform_placeholder
    transform_placeholder >> load_warehouse >> validate_gold >> notify_success
