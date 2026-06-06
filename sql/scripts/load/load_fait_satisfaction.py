"""
Chargement du staging satisfaction dans PostgreSQL.
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
SATISFACTION_FILE = BRONZE_DIR / "satisfaction_raw.csv"

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DATABASE = os.getenv("POSTGRES_DB", "chu_data")
PG_USER = os.getenv("POSTGRES_USER", "chu_admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "chu_password_change_me11")

STAGING_TABLE = "gold.stg_satisfaction_raw"


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


def _to_float_or_none(value: object) -> float | None:
    text = _to_text_or_none(value)
    if text is None:
        return None
    text = text.replace(",", ".")
    return float(text)


def _read_source() -> pd.DataFrame:
    if not SATISFACTION_FILE.exists():
        raise FileNotFoundError(f"Fichier Bronze introuvable: {SATISFACTION_FILE}")

    df = pd.read_csv(SATISFACTION_FILE, dtype=str, sep=None, engine="python", on_bad_lines="skip")
    if df.empty:
        raise ValueError(f"Fichier Bronze vide: {SATISFACTION_FILE}")

    col_map = {_normalize_col(col): col for col in df.columns}
    date_col = _find_column(col_map, ["date_satisfaction", "date", "date_mesure"])
    finess_col = _find_column(col_map, ["finess", "id_etablissement", "etablissement"])
    code_region_col = _find_column(col_map, ["code_region", "region", "region_code"])
    score_col = _find_column(col_map, ["score_global", "score", "note"])

    normalized_rows: list[tuple[str, str, str, float]] = []
    for _, row in df.iterrows():
        date_mesure = _to_date_or_none(row[date_col]) if date_col else None
        finess = _to_text_or_none(row[finess_col]) if finess_col else None
        code_region = _to_text_or_none(row[code_region_col]) if code_region_col else None
        score_global = _to_float_or_none(row[score_col]) if score_col else None

        if date_mesure is None or finess is None or code_region is None or score_global is None:
            continue
        normalized_rows.append((date_mesure, finess, code_region, score_global))

    if not normalized_rows:
        raise ValueError("Aucune ligne satisfaction exploitable apres normalisation")

    return pd.DataFrame(
        normalized_rows,
        columns=["date_mesure_src", "finess_src", "code_region_src", "score_global_src"],
    )


def _get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def load_fait_satisfaction() -> None:
    logger.info("Demarrage chargement staging satisfaction")
    frame = _read_source()

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {STAGING_TABLE} (
                    date_mesure_src DATE NOT NULL,
                    finess_src TEXT NOT NULL,
                    code_region_src TEXT NOT NULL,
                    score_global_src NUMERIC(10, 4) NOT NULL
                )
                """
            )
            cur.execute(f"TRUNCATE TABLE {STAGING_TABLE}")
            execute_values(
                cur,
                f"""
                INSERT INTO {STAGING_TABLE}
                (date_mesure_src, finess_src, code_region_src, score_global_src)
                VALUES %s
                """,
                list(frame.itertuples(index=False, name=None)),
            )

    logger.info("Chargement satisfaction termine avec %s lignes", len(frame))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_fait_satisfaction()
