"""
Utilitaires pour DAGs Airflow

Fonctions helper pour exécuter scripts Python, HiveQL, logging, etc.
"""

import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Logger Airflow
logger = logging.getLogger(__name__)


def log_step(step_name: str, status: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Centralisé logging pour chaque étape du pipeline.
    
    Args:
        step_name: Nom de l'étape (extract, transform, load, etc)
        status: Status (starting, success, failed)
        data: Données additionnelles (rows, errors, etc)
    """
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {step_name.upper()}: {status}"
    
    if data:
        log_msg += f" | {data}"
    
    if status == 'success':
        logger.info(log_msg)
    elif status == 'failed':
        logger.error(log_msg)
    else:
        logger.debug(log_msg)


def run_python_script(script: str, **context) -> None:
    """
    Exécute un script Python standalone.
    
    Args:
        script: Chemin du script Python (/scripts/extract/extract_postgres.py)
        **context: Context Airflow (task_instance, etc)
    """
    try:
        script_name = Path(script).stem
        log_step(script_name, 'starting')
        
        # Exécuter le script
        result = subprocess.run(
            ['python', script],
            cwd='/airflow',
            capture_output=True,
            text=True,
            timeout=3600  # 1h timeout
        )
        
        if result.returncode != 0:
            log_step(script_name, 'failed', {'error': result.stderr})
            raise Exception(f"Script {script} échoué: {result.stderr}")
        
        log_step(script_name, 'success', {'output': result.stdout[:200]})
        
    except subprocess.TimeoutExpired:
        log_step(script_name, 'failed', {'error': 'Timeout (>1h)'})
        raise
    except Exception as e:
        log_step(script_name, 'failed', {'error': str(e)})
        raise


def run_hive_query(sql_file: str, **context) -> None:
    """
    Exécute une requête HiveQL depuis un fichier.
    
    Args:
        sql_file: Chemin du fichier SQL (/scripts/transform/transform_consultations.sql)
        **context: Context Airflow
    """
    try:
        sql_name = Path(sql_file).stem
        log_step(sql_name, 'starting')
        
        # Lire le fichier SQL
        with open(sql_file, 'r') as f:
            query = f.read()
        
        # Exécuter via hive CLI
        result = subprocess.run(
            ['hive', '-e', query],
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode != 0:
            log_step(sql_name, 'failed', {'error': result.stderr})
            raise Exception(f"Requête Hive échouée: {result.stderr}")
        
        log_step(sql_name, 'success', {'output': result.stdout[:200]})
        
    except subprocess.TimeoutExpired:
        log_step(sql_name, 'failed', {'error': 'Timeout (>1h)'})
        raise
    except Exception as e:
        log_step(sql_name, 'failed', {'error': str(e)})
        raise


def validate_table(
    table_name: str,
    checks: Dict[str, Any],
    **context
) -> None:
    """
    Valide une table Hive (nulls, doublons, etc).
    
    Args:
        table_name: Nom table Hive (gold.fait_consultation)
        checks: Dictionnaire de checks {'null_cols': [...], 'unique_cols': [...]}
        **context: Context Airflow
    """
    try:
        log_step(f'validate_{table_name}', 'starting')
        
        # À implémenter: vrai validation checks
        # Pour l'instant, juste log
        
        log_step(f'validate_{table_name}', 'success')
        
    except Exception as e:
        log_step(f'validate_{table_name}', 'failed', {'error': str(e)})
        raise
