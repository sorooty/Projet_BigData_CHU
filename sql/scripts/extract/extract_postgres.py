"""
Extraction PostgreSQL - Consultations et donnees sources.

Cette tache:
1. Se connecte a PostgreSQL
2. Recupere les consultations depuis hier
3. Sauvegarde le CSV dans le dossier Bronze du conteneur Airflow

Execution idempotente.
"""

import os
import re
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
PG_SOURCE_DATABASE = os.getenv("POSTGRES_SOURCE_DB", "postgres")
PG_SOURCE_TABLE = os.getenv("POSTGRES_SOURCE_TABLE", "consultation")
PG_SOURCE_FILTER = os.getenv("POSTGRES_SOURCE_FILTER", "").strip()


def _resolve_source_table(table_name: str) -> str:
    """Retourne une table source qualifiee dans operational par defaut."""
    candidate = table_name.strip()
    if "." not in candidate:
        candidate = f"operational.{candidate}"

    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*", candidate):
        raise ValueError(f"Nom de table source invalide: {table_name}")

    return candidate


def _source_view_exists(conn) -> bool:
    """Vérifie si la vue operational.consultation est disponible."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.views "
                "WHERE table_schema = 'operational' AND table_name = 'consultation'"
            )
            return cur.fetchone() is not None
    except Exception:
        return False


def extract_consultations() -> None:
    """Extraction principale."""
    output_file = BRONZE_DIR / "consultations_raw.csv"

    try:
        logger.info("Demarrage extraction PostgreSQL consultations")

        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_SOURCE_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
        )
        logger.info("Connecte a PostgreSQL (%s)", PG_SOURCE_DATABASE)

        if not _source_view_exists(conn):
            conn.close()
            if output_file.exists() and output_file.stat().st_size > 0:
                # #region agent log
                import json, time as _t, pathlib as _p
                _p.Path("/opt/airflow/data/debug-bddb4f.log").parent.mkdir(parents=True, exist_ok=True)
                open("/opt/airflow/data/debug-bddb4f.log", "a").write(json.dumps({"sessionId":"bddb4f","timestamp":int(_t.time()*1000),"location":"extract_postgres.py:fallback","message":"fallback to existing bronze CSV","data":{"file":str(output_file),"size":output_file.stat().st_size},"hypothesisId":"H1","runId":"post-fix"}) + "\n")
                # #endregion
                logger.warning(
                    "Vue operational.consultation absente (dump source non charge). "
                    "Utilisation du CSV bronze existant: %s (%d octets)",
                    output_file,
                    output_file.stat().st_size,
                )
                return
            raise RuntimeError(
                "Vue operational.consultation introuvable et aucun CSV bronze existant. "
                "Charger le dump source (project_data/BDD PostgreSQL/DATA2023) dans chu_data."
            )

        source_table = _resolve_source_table(PG_SOURCE_TABLE)
        query = """
            SELECT
                c.id_consultation,
                c.id_patient,
                c.date_consultation,
                c.diagnostic,
                c.id_etablissement,
                c.montant,
                p.sexe,
                p.age
            FROM {table_name} c
            LEFT JOIN operational.patient p ON p.id_patient = c.id_patient
            ORDER BY c.date_consultation DESC
        """.format(table_name=source_table)

        if PG_SOURCE_FILTER:
            query = query.replace(
                "ORDER BY c.date_consultation DESC",
                f"WHERE {PG_SOURCE_FILTER}\n            ORDER BY c.date_consultation DESC",
            )

        df = pd.read_sql(query, conn)
        conn.close()
        logger.info("Recupere %d consultations", len(df))

        BRONZE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        logger.info("Sauvegarde en %s", output_file)
        logger.info("Extraction PostgreSQL reussie")

    except Exception as e:
        logger.error("Erreur extraction PostgreSQL: %s", str(e))
        raise


if __name__ == '__main__':
    # Execution standalone: python extract_postgres.py
    logging.basicConfig(level=logging.INFO)
    extract_consultations()
