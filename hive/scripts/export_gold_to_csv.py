"""
Export des tables Gold PostgreSQL vers CSV pour chargement HDFS.

Usage:
    python export_gold_to_csv.py

Les CSV sont deposes dans /tmp/gold_export/ (ou GOLD_EXPORT_DIR).
Ensuite: hdfs dfs -put /tmp/gold_export/gold/ /chu/data/gold/
"""

import os
import logging
import psycopg2
from pathlib import Path

logger = logging.getLogger(__name__)

PG_HOST     = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT     = os.getenv("POSTGRES_PORT", "5432")
PG_DATABASE = os.getenv("POSTGRES_DB", "chu_data")
PG_USER     = os.getenv("POSTGRES_USER", "chu_admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

EXPORT_DIR = Path(os.getenv("GOLD_EXPORT_DIR", "/tmp/gold_export"))

TABLES = [
    "gold.dim_temps",
    "gold.dim_patient",
    "gold.dim_geographie",
    "gold.dim_etablissement",
    "gold.dim_diagnostic",
    "gold.dim_professionnel",
    "gold.fait_consultation",
    "gold.fait_deces",
    "gold.fait_satisfaction",
]


def export_table(cur, table: str, dest: Path) -> None:
    name = table.split(".")[1]
    dest.mkdir(parents=True, exist_ok=True)
    output_file = dest / f"{name}.csv"

    with output_file.open("w", newline="", encoding="utf-8") as f:
        cur.copy_expert(
            f"COPY {table} TO STDOUT WITH (FORMAT csv, HEADER true)",
            f,
        )
    logger.info("Exporte %s -> %s", table, output_file)


def main():
    logging.basicConfig(level=logging.INFO)

    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname=PG_DATABASE, user=PG_USER, password=PG_PASSWORD,
    )
    try:
        with conn.cursor() as cur:
            for table in TABLES:
                export_table(cur, table, EXPORT_DIR / "gold")
    finally:
        conn.close()

    logger.info("Export termine. Depot HDFS: hdfs dfs -put %s/gold/ /chu/data/gold/", EXPORT_DIR)


if __name__ == "__main__":
    main()
