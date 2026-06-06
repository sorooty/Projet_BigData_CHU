"""
Chargement du staging geographie dans PostgreSQL.
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
GEOGRAPHIE_FILE = BRONZE_DIR / "geographie_raw.csv"

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DATABASE = os.getenv("POSTGRES_DB", "chu_data")
PG_USER = os.getenv("POSTGRES_USER", "chu_admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "chu_password_change_me11")

STAGING_TABLE = "gold.stg_geographie_raw"


def _normalize_col(name: str) -> str:
    return "".join(ch for ch in str(name).strip().lower() if ch.isalnum())


def _find_column(col_map: Dict[str, str], aliases: list[str]) -> str | None:
    for alias in aliases:
        key = _normalize_col(alias)
        if key in col_map:
            return col_map[key]
    return None


def _to_int_or_none(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return int(float(text))


def _to_text_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _read_source() -> pd.DataFrame:
    if not GEOGRAPHIE_FILE.exists():
        raise FileNotFoundError(f"Fichier Bronze introuvable: {GEOGRAPHIE_FILE}")

    df = pd.read_csv(GEOGRAPHIE_FILE, dtype=str, sep=None, engine="python", on_bad_lines="skip")
    if df.empty:
        raise ValueError(f"Fichier Bronze vide: {GEOGRAPHIE_FILE}")

    col_map = {_normalize_col(col): col for col in df.columns}
    id_geo_col = _find_column(col_map, ["id_geo", "id_region", "id"])
    code_region_col = _find_column(col_map, ["code_region", "region", "region_code", "code_reg"])
    libelle_region_col = _find_column(col_map, ["libelle_region", "nom_region", "region_label", "region"])
    pays_col = _find_column(col_map, ["pays", "country"])

    normalized_rows: list[tuple[int, str, str, str]] = []
    for idx, row in df.iterrows():
        id_geo = _to_int_or_none(row[id_geo_col]) if id_geo_col else idx + 1
        code_region = _to_text_or_none(row[code_region_col]) if code_region_col else None
        libelle_region = _to_text_or_none(row[libelle_region_col]) if libelle_region_col else None
        pays = _to_text_or_none(row[pays_col]) if pays_col else "FRANCE"

        if code_region is None:
            continue
        normalized_rows.append((id_geo, code_region, libelle_region, pays))

    if not normalized_rows:
        raise ValueError("Aucune ligne geographie exploitable apres normalisation")

    return pd.DataFrame(
        normalized_rows,
        columns=["id_geo_src", "code_region_src", "libelle_region_src", "pays_src"],
    )


def _get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def load_dim_geographie() -> None:
    logger.info("Demarrage chargement staging geographie")
    frame = _read_source()

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {STAGING_TABLE} (
                    id_geo_src INT NOT NULL,
                    code_region_src TEXT NOT NULL,
                    libelle_region_src TEXT,
                    pays_src TEXT
                )
                """
            )
            cur.execute(f"TRUNCATE TABLE {STAGING_TABLE}")
            execute_values(
                cur,
                f"""
                INSERT INTO {STAGING_TABLE}
                (id_geo_src, code_region_src, libelle_region_src, pays_src)
                VALUES %s
                """,
                list(frame.itertuples(index=False, name=None)),
            )

    logger.info("Chargement geographie termine avec %s lignes", len(frame))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dim_geographie()
