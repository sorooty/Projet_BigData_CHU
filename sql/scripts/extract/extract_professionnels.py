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
RAW_DIR = DATA_ROOT / "raw"

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

    frame = None
    try:
        with _get_connection() as conn:
            frame = pd.read_sql(query, conn)
    except Exception as exc:
        logger.warning("Extraction professionnels via PostgreSQL indisponible: %s", exc)

    if frame is None or frame.empty:
        files = (
            sorted(RAW_DIR.glob("*professionnel*.csv"))
            + sorted(RAW_DIR.glob("*professionnels*.csv"))
            + sorted(BRONZE_DIR.glob("*professionnel*.csv"))
            + sorted(BRONZE_DIR.glob("*professionnels*.csv"))
        )
        if not files:
            raise ValueError("Aucune source professionnels disponible (PostgreSQL ou CSV)")

        source = files[0]
        logger.info("Fallback extraction professionnels depuis %s", source.name)
        raw = pd.read_csv(source, dtype=str, sep=None, engine="python", on_bad_lines="skip")
        if raw.empty:
            raise ValueError(f"Fichier professionnels vide: {source}")

        cols = {c.lower().strip(): c for c in raw.columns}
        id_col = None
        for key in ["id_professionnel", "id_prof_source", "id_prof", "id", "identifiant"]:
            if key in cols:
                id_col = cols[key]
                break
        if id_col is None:
            raise ValueError("Colonne id professionnel introuvable dans la source CSV")

        nom_col = None
        for key in ["nom_source", "nom", "professionnel", "nom_prenom"]:
            if key in cols:
                nom_col = cols[key]
                break

        frame = pd.DataFrame(
            {
                "id_prof_source": raw[id_col],
                "nom_source": raw[nom_col] if nom_col else "",
            }
        )

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
