"""
Chargement du staging consultations dans PostgreSQL.

Cette tache:
1. Lit le CSV Bronze produit par l'extraction PostgreSQL
2. Recharge une table de staging dans le schema gold
3. Prepare les donnees pour la transformation suivante
"""

import logging
import os
from pathlib import Path

import psycopg2

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
BRONZE_DIR = DATA_ROOT / "bronze"
CONSULTATIONS_FILE = BRONZE_DIR / "consultations_raw.csv"

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DATABASE = os.getenv("POSTGRES_DB", "chu_data")
PG_USER = os.getenv("POSTGRES_USER", "chu_admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "chu_password_change_me11")

STAGING_TABLE = "gold.stg_consultations_raw"


def _get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def load_to_warehouse() -> None:
    """Charge le bronze dans la zone de staging PostgreSQL."""
    if not CONSULTATIONS_FILE.exists():
        raise FileNotFoundError(f"Fichier Bronze introuvable: {CONSULTATIONS_FILE}")

    logger.info("Demarrage du chargement du staging consultations")

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS gold")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {STAGING_TABLE} (
                    id_consultation TEXT,
                    id_patient TEXT NOT NULL,
                    date_consultation DATE NOT NULL,
                    diagnostic TEXT,
                    id_etablissement TEXT NOT NULL,
                    montant NUMERIC(12, 2),
                    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(f"TRUNCATE TABLE {STAGING_TABLE}")

            with CONSULTATIONS_FILE.open("r", encoding="utf-8", newline="") as stream:
                cur.copy_expert(
                    f"""
                    COPY {STAGING_TABLE} (
                        id_consultation,
                        id_patient,
                        date_consultation,
                        diagnostic,
                        id_etablissement,
                        montant
                    ) FROM STDIN WITH (FORMAT csv, HEADER true)
                    """,
                    stream,
                )

            cur.execute(f"SELECT COUNT(*) FROM {STAGING_TABLE}")
            row_count = cur.fetchone()[0]

    logger.info("Chargement staging termine avec %s lignes", row_count)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_to_warehouse()
