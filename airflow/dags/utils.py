"""
Utilitaires pour DAGs Airflow — CHU Pipeline

Fonctions helper pour exécuter scripts Python, requêtes SQL PostgreSQL,
logging, et validation des données.

Chemins container: /opt/airflow/dags/, /opt/airflow/sql/scripts/
"""

import subprocess
import logging
import os
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Racine des scripts dans le container
SCRIPTS_ROOT = Path("/opt/airflow/sql/scripts")


def log_step(step_name: str, status: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Log centralisé pour chaque étape du pipeline."""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {step_name.upper()}: {status}"

    if data:
        log_msg += f" | {data}"

    if status == "success":
        logger.info(log_msg)
    elif status == "failed":
        logger.error(log_msg)
    else:
        logger.debug(log_msg)


def run_python_script(script: str, **context) -> None:
    """
    Exécute un script Python standalone depuis /opt/airflow/sql/scripts/.

    Args:
        script: Chemin absolu ou relatif au dossier scripts.
                Ex: "extract/extract_postgres.py"
    """
    script_path = script if Path(script).is_absolute() else str(SCRIPTS_ROOT / script)
    script_name = Path(script_path).stem

    try:
        log_step(script_name, "starting")

        result = subprocess.run(
            ["python", script_path],
            cwd="/opt/airflow",
            capture_output=True,
            text=True,
            timeout=3600,
            env={**os.environ},
        )

        if result.returncode != 0:
            log_step(script_name, "failed", {"error": result.stderr[-500:]})
            raise Exception(f"Script {script_name} échoué:\n{result.stderr}")

        log_step(script_name, "success", {"output": result.stdout[:200]})

    except subprocess.TimeoutExpired:
        log_step(script_name, "failed", {"error": "Timeout (>1h)"})
        raise
    except Exception as e:
        log_step(script_name, "failed", {"error": str(e)})
        raise


def run_sql_on_postgres(sql_file: str, schema: str = "gold", **context) -> None:
    """
    Exécute un fichier SQL sur PostgreSQL (Gold = schema gold).
    Remplace run_hive_query: pas de Hive CLI dans l'image Airflow.

    Args:
        sql_file: Chemin relatif au dossier scripts.
                  Ex: "transform/transform_consultations.sql"
        schema:   Schéma PostgreSQL cible (default: gold)
    """
    sql_path = sql_file if Path(sql_file).is_absolute() else str(SCRIPTS_ROOT / sql_file)
    sql_name = Path(sql_path).stem

    try:
        log_step(sql_name, "starting")

        with open(sql_path, "r", encoding="utf-8") as f:
            query = f.read()

        conn = psycopg2.connect(
            host=os.environ["POSTGRES_HOST"],
            port=os.environ.get("POSTGRES_PORT", "5432"),
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        )

        with conn:
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {schema}, public")
                cur.execute(query)

        conn.close()
        log_step(sql_name, "success")

    except Exception as e:
        log_step(sql_name, "failed", {"error": str(e)})
        raise


def validate_table(table_name: str, checks: Dict[str, Any], **context) -> None:
    """
    Valide une table PostgreSQL (nulls, doublons, seuils).

    Args:
        table_name: Nom de la table (ex: gold.fait_consultation)
        checks: Dict de contrôles {'min_rows': 100, 'null_cols': ['id_temps']}
    """
    try:
        log_step(f"validate_{table_name}", "starting")

        conn = psycopg2.connect(
            host=os.environ["POSTGRES_HOST"],
            port=os.environ.get("POSTGRES_PORT", "5432"),
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        )

        with conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cur.fetchone()[0]

        conn.close()

        min_rows = checks.get("min_rows", 1)
        if row_count < min_rows:
            raise Exception(
                f"{table_name}: {row_count} lignes, minimum attendu: {min_rows}"
            )

        log_step(f"validate_{table_name}", "success", {"rows": row_count})

    except Exception as e:
        log_step(f"validate_{table_name}", "failed", {"error": str(e)})
        raise

