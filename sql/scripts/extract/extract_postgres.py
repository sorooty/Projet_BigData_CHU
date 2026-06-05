"""
Extraction PostgreSQL - Consultations et donnees sources.

Cette tache:
1. Se connecte a PostgreSQL
2. Recupere les consultations depuis hier
3. Sauvegarde le CSV dans le dossier Bronze du conteneur Airflow

Execution idempotente.
"""

import os
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
PG_SOURCE_TABLE = os.getenv("POSTGRES_SOURCE_TABLE", "consultation")


def extract_consultations() -> None:
    """Extraction principale."""
    try:
        logger.info("Demarrage extraction PostgreSQL consultations")
        
        # Connexion PostgreSQL
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        logger.info("Connecte a PostgreSQL")
        
        # Requete configurable depuis l'environnement
        query = """
            SELECT 
                id_consultation,
                id_patient,
                date_consultation,
                diagnostic,
                id_etablissement,
                montant
            FROM {table_name}
            WHERE date_consultation >= CURRENT_DATE - INTERVAL '1 day'
            ORDER BY date_consultation DESC
        """.format(table_name=PG_SOURCE_TABLE)
        
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
