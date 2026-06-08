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
import os

# utils.py est dans /opt/airflow/dags, déjà sur le PYTHONPATH Airflow
from utils import run_python_script, run_sql_on_postgres, log_step

default_args = {
    "owner": "chu_team",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2025, 1, 1),
}

ENABLE_EXTENDED_FACTS = os.getenv("ENABLE_EXTENDED_FACTS", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

with DAG(
    "chu_daily_pipeline",
    default_args=default_args,
    description="Pipeline quotidien CHU: Extract, Load, Transform, Validate",
    schedule_interval="0 0 * * *",
    catchup=False,
    max_active_runs=1,
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

    if ENABLE_EXTENDED_FACTS:
        extract_etablissements = PythonOperator(
            task_id="extract_etablissements",
            python_callable=run_python_script,
            op_kwargs={"script": "extract/extract_etablissements.py"},
            doc_md="Extraction etablissements vers Bronze",
        )

        extract_professionnels = PythonOperator(
            task_id="extract_professionnels",
            python_callable=run_python_script,
            op_kwargs={"script": "extract/extract_professionnels.py"},
            doc_md="Extraction professionnels vers Bronze",
        )

        extract_deces = PythonOperator(
            task_id="extract_deces",
            python_callable=run_python_script,
            op_kwargs={"script": "extract/extract_deces.py"},
            doc_md="Extraction deces vers Bronze",
        )

        extract_satisfaction = PythonOperator(
            task_id="extract_satisfaction",
            python_callable=run_python_script,
            op_kwargs={"script": "extract/extract_satisfaction.py"},
            doc_md="Extraction satisfaction vers Bronze",
        )

        extract_geographie = PythonOperator(
            task_id="extract_geographie",
            python_callable=run_python_script,
            op_kwargs={"script": "extract/extract_geographie.py"},
            doc_md="Extraction geographie vers Bronze",
        )

        load_dim_geographie = PythonOperator(
            task_id="load_dim_geographie",
            python_callable=run_python_script,
            op_kwargs={"script": "load/load_dim_geographie.py"},
            doc_md="Chargement du staging geographie depuis Bronze vers PostgreSQL",
        )

        load_stg_etablissements = PythonOperator(
            task_id="load_stg_etablissements",
            python_callable=run_python_script,
            op_kwargs={"script": "load/load_stg_etablissements.py"},
            doc_md="Chargement du staging etablissements depuis Bronze vers PostgreSQL",
        )

        load_stg_professionnels = PythonOperator(
            task_id="load_stg_professionnels",
            python_callable=run_python_script,
            op_kwargs={"script": "load/load_stg_professionnels.py"},
            doc_md="Chargement du staging professionnels depuis Bronze vers PostgreSQL",
        )

        transform_dim_geographie = PythonOperator(
            task_id="transform_dim_geographie",
            python_callable=run_sql_on_postgres,
            op_kwargs={
                "sql_file": "transform/transform_dim_geographie.sql",
                "schema": "gold",
            },
            doc_md="Transformation et alimentation de la dimension geographie",
        )

        transform_dim_etablissement = PythonOperator(
            task_id="transform_dim_etablissement",
            python_callable=run_sql_on_postgres,
            op_kwargs={
                "sql_file": "transform/dim_etablissement.sql",
                "schema": "gold",
            },
            doc_md="Transformation et alimentation de la dimension etablissement",
        )

        transform_dim_professionnel = PythonOperator(
            task_id="transform_dim_professionnel",
            python_callable=run_sql_on_postgres,
            op_kwargs={
                "sql_file": "transform/dim_professionnel.sql",
                "schema": "gold",
            },
            doc_md="Transformation et alimentation de la dimension professionnel",
        )

        load_fait_deces = PythonOperator(
            task_id="load_fait_deces",
            python_callable=run_python_script,
            op_kwargs={"script": "load/load_fait_deces.py"},
            doc_md="Chargement du staging deces depuis Bronze vers PostgreSQL",
        )

        transform_fait_deces = PythonOperator(
            task_id="transform_fait_deces",
            python_callable=run_sql_on_postgres,
            op_kwargs={
                "sql_file": "transform/transform_fait_deces.sql",
                "schema": "gold",
            },
            doc_md="Transformation et alimentation de la table de faits deces",
        )

        load_fait_satisfaction = PythonOperator(
            task_id="load_fait_satisfaction",
            python_callable=run_python_script,
            op_kwargs={"script": "load/load_fait_satisfaction.py"},
            doc_md="Chargement du staging satisfaction depuis Bronze vers PostgreSQL",
        )

        transform_fait_satisfaction = PythonOperator(
            task_id="transform_fait_satisfaction",
            python_callable=run_sql_on_postgres,
            op_kwargs={
                "sql_file": "transform/transform_fait_satisfaction.sql",
                "schema": "gold",
            },
            doc_md="Transformation et alimentation de la table de faits satisfaction",
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
    load_staging_consultations >> transform_consultations

    if ENABLE_EXTENDED_FACTS:
        extract_csv >> [extract_etablissements, extract_deces, extract_satisfaction]
        extract_postgres >> extract_professionnels

        extract_etablissements >> load_stg_etablissements
        extract_professionnels >> load_stg_professionnels

        [extract_deces, extract_satisfaction] >> extract_geographie

        [transform_consultations, extract_geographie] >> load_dim_geographie >> transform_dim_geographie
        [transform_dim_geographie, load_stg_etablissements] >> transform_dim_etablissement
        load_stg_professionnels >> transform_dim_professionnel

        transform_dim_geographie >> load_fait_deces >> transform_fait_deces
        transform_dim_geographie >> load_fait_satisfaction >> transform_fait_satisfaction
        [transform_consultations, transform_dim_etablissement, transform_dim_professionnel, transform_fait_deces, transform_fait_satisfaction] >> validate_gold
    else:
        transform_consultations >> validate_gold

    validate_gold >> notify_success
