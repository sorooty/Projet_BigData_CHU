"""
DAG principal CHU - Orchestration pipeline quotidien

Ce DAG orchestre:
1. Extract: récupération des données PostgreSQL, CSV, FTP
2. Transform: transformations HiveQL (dimensions, faits)
3. Validate: validation qualité
4. Notify: alertes (Slack, email)

Schedule: Quotidien à minuit (0 0 * * *)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

# Imports des utils
sys.path.insert(0, '/airflow/dags')
from utils import run_python_script, run_hive_query, log_step

# Config par défaut
default_args = {
    'owner': 'chu_team',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 1, 1),
}

# DAG Principal
with DAG(
    'chu_daily_pipeline',
    default_args=default_args,
    description='Pipeline quotidien CHU: Extract → Transform → Load → Validate',
    schedule_interval='0 0 * * *',  # Quotidien minuit
    catchup=False,
    tags=['chu', 'production']
) as dag:
    
    # ============ PHASE 1: EXTRACT (Parallèle) ============
    
    extract_postgres = PythonOperator(
        task_id='extract_postgres',
        python_callable=run_python_script,
        op_kwargs={'script': '/scripts/extract/extract_postgres.py'},
        doc='Extraction PostgreSQL (consultations, patients, etc) → CSV Bronze',
    )
    
    extract_csv = PythonOperator(
        task_id='extract_csv',
        python_callable=run_python_script,
        op_kwargs={'script': '/scripts/extract/extract_csv.py'},
        doc='Extraction CSV sources (établissements, etc) → CSV Bronze',
    )
    
    # ============ PHASE 2: TRANSFORM (Séquentiel) ============
    
    # Les tâches de transformation seront ajoutées ici par Seyni
    # transform_dimensions (dim_patient, dim_etablissement, etc)
    # transform_faits (fait_consultation, fait_hospitalisation, etc)
    
    # Stub pour structure:
    transform_placeholder = PythonOperator(
        task_id='transform_placeholder',
        python_callable=lambda: log_step('transform', 'placeholder'),
        doc='Placeholder - sera remplacé par vrai transformations',
    )
    
    # ============ PHASE 3: LOAD ============
    
    load_warehouse = PythonOperator(
        task_id='load_warehouse',
        python_callable=run_python_script,
        op_kwargs={'script': '/scripts/load/load_to_warehouse.py'},
        doc='Chargement dans Hive/Gold (tables faits + dimensions)',
    )
    
    # ============ PHASE 4: VALIDATE ============
    
    validate_gold = PythonOperator(
        task_id='validate_gold',
        python_callable=run_python_script,
        op_kwargs={'script': '/scripts/validate_gold.py'},
        doc='Validation qualité données Gold (nulls, doublons, etc)',
    )
    
    # ============ PHASE 5: NOTIFY ============
    
    notify_success = PythonOperator(
        task_id='notify_success',
        python_callable=lambda: log_step('pipeline', 'success'),
        trigger_rule='all_success',
        doc='Notification succès (optional: Slack)',
    )
    
    # ============ ORCHESTRATION: Dépendances ============
    
    # Extract parallèle
    [extract_postgres, extract_csv] >> transform_placeholder
    
    # Transform → Load → Validate → Notify
    transform_placeholder >> load_warehouse >> validate_gold >> notify_success
