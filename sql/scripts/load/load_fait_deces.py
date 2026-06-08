"""
Chargement du staging deces dans PostgreSQL.

Stratégie : lecture chunked du bronze CSV (24M+ lignes), agrégation
date+région en Python, puis INSERT de seulement ~quelques milliers de
lignes en staging → transform SQL (SUM) inchangé.
"""

import logging
import os
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

DATA_ROOT  = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
BRONZE_DIR = DATA_ROOT / "bronze"
DECES_FILE = BRONZE_DIR / "deces_raw.csv"

PG_HOST     = os.getenv("POSTGRES_HOST",     "postgres")
PG_PORT     = os.getenv("POSTGRES_PORT",     "5432")
PG_DATABASE = os.getenv("POSTGRES_DB",       "chu_data")
PG_USER     = os.getenv("POSTGRES_USER",     "chu_admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "chu_password_change_me11")

STAGING_TABLE = "gold.stg_deces_raw"
CHUNK_SIZE    = 500_000


def _get_connection():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname=PG_DATABASE, user=PG_USER, password=PG_PASSWORD,
    )


def _aggregate_bronze() -> pd.DataFrame:
    """Lit deces_raw.csv par chunks et renvoie un DataFrame agrégé
    (date_deces_src, code_region_src) → nb_deces_src (count)."""
    if not DECES_FILE.exists():
        raise FileNotFoundError(f"Fichier Bronze introuvable : {DECES_FILE}")

    agg: dict[tuple, int] = {}

    for i, chunk in enumerate(pd.read_csv(
        DECES_FILE, dtype=str, sep=",", on_bad_lines="skip",
        usecols=["date_deces", "code_region"], chunksize=CHUNK_SIZE,
    )):
        chunk = chunk.dropna(subset=["date_deces", "code_region"])
        chunk["date_deces"]   = chunk["date_deces"].str.strip().str[:10]
        chunk["code_region"]  = chunk["code_region"].str.strip()
        chunk = chunk[chunk["date_deces"].str.len() == 10]
        chunk = chunk[chunk["code_region"].str.len() > 0]

        for key, cnt in chunk.groupby(["date_deces", "code_region"]).size().items():
            agg[key] = agg.get(key, 0) + int(cnt)

        if i % 10 == 0:
            logger.info("Chunk %s lu — %s paires distinctes accumulées", i, len(agg))

    if not agg:
        raise ValueError("Aucune ligne deces exploitable après agrégation")

    rows = [(d, r, n) for (d, r), n in agg.items()]
    df = pd.DataFrame(rows, columns=["date_deces_src", "code_region_src", "nb_deces_src"])
    logger.info("Agrégation terminée : %s lignes de staging", len(df))
    return df


def load_fait_deces() -> None:
    logger.info("Demarrage chargement staging deces")
    frame = _aggregate_bronze()

    with _get_connection() as conn:
        with conn.cursor() as cur:
            # Recréer la table pour s'assurer que le schéma est à jour
            # (l'ancienne version avait id_patient_src qui n'existe plus)
            cur.execute(f"DROP TABLE IF EXISTS {STAGING_TABLE} CASCADE")
            cur.execute(f"""
                CREATE TABLE {STAGING_TABLE} (
                    date_deces_src  DATE NOT NULL,
                    code_region_src TEXT NOT NULL,
                    nb_deces_src    INT  NOT NULL
                )
            """)
            execute_values(
                cur,
                f"""
                INSERT INTO {STAGING_TABLE}
                    (date_deces_src, code_region_src, nb_deces_src)
                VALUES %s
                """,
                list(frame.itertuples(index=False, name=None)),
                page_size=1000,
            )
        conn.commit()

    logger.info("Chargement deces terminé avec %s lignes de staging", len(frame))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_fait_deces()
