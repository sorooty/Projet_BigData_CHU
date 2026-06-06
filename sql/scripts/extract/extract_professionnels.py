"""
Extraction des professionnels de sante vers la zone Bronze.
"""

import logging
import os
from pathlib import Path

import pandas as pd
import psycopg2

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
BRONZE_DIR = DATA_ROOT / "bronze"

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DATABASE = os.getenv("POSTGRES_SOURCE_DB", os.getenv("POSTGRES_DB", "chu_data"))
PG_USER = os.getenv("POSTGRES_USER", "chu_admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "chu_password_change_me11")


def _get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def extract_professionnels() -> None:
    logger.info("Demarrage extraction professionnels")
    query = """
        SELECT
            id_professionnel::TEXT AS id_prof_source,
            TRIM(CONCAT(COALESCE(nom, ''), ' ', COALESCE(prenom, ''))) AS nom_source
        FROM operational.professionnel_de_sante
        WHERE id_professionnel IS NOT NULL
    """

    with _get_connection() as conn:
        frame = pd.read_sql(query, conn)

    frame["id_prof_source"] = frame["id_prof_source"].astype(str).str.strip()
    frame["nom_source"] = frame["nom_source"].fillna("").astype(str).str.strip()
    frame = frame[frame["id_prof_source"] != ""]

    if frame.empty:
        raise ValueError("Aucune ligne professionnels exploitable apres normalisation")

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    output = BRONZE_DIR / "professionnels_raw.csv"
    frame.to_csv(output, index=False)
    logger.info("Extraction professionnels terminee avec %s lignes vers %s", len(frame), output.name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extract_professionnels()
