"""
Chargement du staging professionnels dans PostgreSQL.
"""

import logging
import os
from pathlib import Path

import psycopg2

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
BRONZE_DIR = DATA_ROOT / "bronze"
SOURCE_FILE = BRONZE_DIR / "professionnels_raw.csv"

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DATABASE = os.getenv("POSTGRES_DB", "chu_data")
PG_USER = os.getenv("POSTGRES_USER", "chu_admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

STAGING_TABLE = "gold.stg_professionnels_raw"


def _get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def load_staging_professionnels() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Fichier Bronze introuvable: {SOURCE_FILE}")

    logger.info("Demarrage chargement staging professionnels")
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {STAGING_TABLE} (
                    id_prof_source VARCHAR NOT NULL,
                    nom_source VARCHAR
                )
                """
            )
            cur.execute(f"TRUNCATE TABLE {STAGING_TABLE}")

            with SOURCE_FILE.open("r", encoding="utf-8", newline="") as stream:
                cur.copy_expert(
                    f"""
                    COPY {STAGING_TABLE} (id_prof_source, nom_source)
                    FROM STDIN WITH (FORMAT csv, HEADER true)
                    """,
                    stream,
                )

    logger.info("Chargement staging professionnels termine")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_staging_professionnels()
