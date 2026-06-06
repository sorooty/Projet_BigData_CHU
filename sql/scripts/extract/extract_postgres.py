"""
Extraction PostgreSQL - Consultations et donnees sources.

Cette tache:
1. Se connecte a PostgreSQL
2. Recupere les consultations depuis hier
3. Sauvegarde le CSV dans le dossier Bronze du conteneur Airflow

Execution idempotente.
"""

import os
import re
import psycopg2
import pandas as pd
from pathlib import Path
import logging

# Logger
logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
BRONZE_DIR = DATA_ROOT / "bronze"

# Config PostgreSQL (depuis env)
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_USER = os.getenv("POSTGRES_USER", "chu_admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "chu_password_change_me11")
PG_DATABASE = os.getenv("POSTGRES_DB", "chu_data")
PG_SOURCE_DATABASE = os.getenv("POSTGRES_SOURCE_DB", "postgres")
PG_SOURCE_TABLE = os.getenv("POSTGRES_SOURCE_TABLE", "consultation")
PG_SOURCE_FILTER = os.getenv("POSTGRES_SOURCE_FILTER", "").strip()


def _resolve_source_table(table_name: str) -> str:
    """Retourne une table source qualifiee dans operational par defaut."""
    candidate = table_name.strip()
    if "." not in candidate:
        candidate = f"operational.{candidate}"

    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*", candidate):
        raise ValueError(f"Nom de table source invalide: {table_name}")

    return candidate


def extract_consultations() -> None:
    """Extraction principale."""
    try:
        logger.info("Demarrage extraction PostgreSQL consultations")
        
        # Connexion PostgreSQL
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_SOURCE_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        logger.info("Connecte a PostgreSQL")
        
        # Requete configurable depuis l'environnement
        source_table = _resolve_source_table(PG_SOURCE_TABLE)
        query = """
            SELECT 
                c.id_consultation,
                c.id_patient,
                c.date_consultation,
                c.diagnostic,
                c.id_etablissement,
                c.montant,
                p.sexe,
                p.age
            FROM {table_name} c
            LEFT JOIN operational.patient p ON p.id_patient = c.id_patient
            ORDER BY c.date_consultation DESC
        """.format(table_name=source_table)

        if PG_SOURCE_FILTER:
            query = query.replace(
                "            ORDER BY date_consultation DESC",
                f"            WHERE {PG_SOURCE_FILTER}\n            ORDER BY date_consultation DESC",
            )
        
        df = pd.read_sql(query, conn)
        logger.info(f"Recupere {len(df)} consultations")
        
        BRONZE_DIR.mkdir(parents=True, exist_ok=True)

        # Sauvegarder en CSV
        output_file = BRONZE_DIR / "consultations_raw.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"Sauvegarde en {output_file}")
        
        conn.close()
        logger.info("Extraction PostgreSQL reussie")
        
    except Exception as e:
        logger.error(f"Erreur extraction PostgreSQL: {str(e)}")
        raise


if __name__ == '__main__':
    # Execution standalone: python extract_postgres.py
    logging.basicConfig(level=logging.INFO)
    extract_consultations()
