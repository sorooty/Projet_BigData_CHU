"""
Chargement du staging deces dans PostgreSQL.
"""

import logging
import os
from pathlib import Path
from typing import Dict

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
BRONZE_DIR = DATA_ROOT / "bronze"
DECES_FILE = BRONZE_DIR / "deces_raw.csv"

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DATABASE = os.getenv("POSTGRES_DB", "chu_data")
PG_USER = os.getenv("POSTGRES_USER", "chu_admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "chu_password_change_me11")

STAGING_TABLE = "gold.stg_deces_raw"


def _normalize_col(name: str) -> str:
    return "".join(ch for ch in str(name).strip().lower() if ch.isalnum())


def _find_column(col_map: Dict[str, str], aliases: list[str]) -> str | None:
    for alias in aliases:
        key = _normalize_col(alias)
        if key in col_map:
            return col_map[key]
    return None


def _to_text_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_date_or_none(value: object) -> str | None:
    text = _to_text_or_none(value)
    if text is None:
        return None
    return text[:10]


def _to_int_or_default(value: object, default: int) -> int:
    text = _to_text_or_none(value)
    if text is None:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def _read_source() -> pd.DataFrame:
    if not DECES_FILE.exists():
        raise FileNotFoundError(f"Fichier Bronze introuvable: {DECES_FILE}")

    df = pd.read_csv(DECES_FILE, dtype=str, sep=None, engine="python", on_bad_lines="skip")
    if df.empty:
        raise ValueError(f"Fichier Bronze vide: {DECES_FILE}")

    col_map = {_normalize_col(col): col for col in df.columns}
    date_col = _find_column(col_map, ["date_deces", "date", "date_mort"])
    patient_col = _find_column(col_map, ["id_patient", "patient_id", "patient"])
    code_region_col = _find_column(col_map, ["code_region", "region", "region_code"])
    nb_deces_col = _find_column(col_map, ["nb_deces", "nombre_deces", "deces"])

    normalized_rows: list[tuple[str, str, str, int]] = []
    for _, row in df.iterrows():
        date_deces = _to_date_or_none(row[date_col]) if date_col else None
        id_patient = _to_text_or_none(row[patient_col]) if patient_col else None
        code_region = _to_text_or_none(row[code_region_col]) if code_region_col else None
        nb_deces = _to_int_or_default(row[nb_deces_col], 1) if nb_deces_col else 1

        if date_deces is None or id_patient is None or code_region is None:
            continue
        normalized_rows.append((date_deces, id_patient, code_region, nb_deces))

    if not normalized_rows:
        raise ValueError("Aucune ligne deces exploitable apres normalisation")

    return pd.DataFrame(
        normalized_rows,
        columns=["date_deces_src", "id_patient_src", "code_region_src", "nb_deces_src"],
    )


def _get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def load_fait_deces() -> None:
    logger.info("Demarrage chargement staging deces")
    frame = _read_source()

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {STAGING_TABLE} (
                    date_deces_src DATE NOT NULL,
                    id_patient_src TEXT NOT NULL,
                    code_region_src TEXT NOT NULL,
                    nb_deces_src INT NOT NULL
                )
                """
            )
            cur.execute(f"TRUNCATE TABLE {STAGING_TABLE}")
            execute_values(
                cur,
                f"""
                INSERT INTO {STAGING_TABLE}
                (date_deces_src, id_patient_src, code_region_src, nb_deces_src)
                VALUES %s
                """,
                list(frame.itertuples(index=False, name=None)),
            )

    logger.info("Chargement deces termine avec %s lignes", len(frame))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_fait_deces()
