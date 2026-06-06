"""
Validation qualité - Vérifie les données Gold

Cette tâche:
1. Vérifie les tables existantes
2. Check nulls, doublons
3. Valide les contraintes métier

À développer selon besoins.
"""

import logging
import os
from pyhive.hive import connect

logger = logging.getLogger(__name__)

HIVE_HOST = os.getenv("HIVE_HOST", "hive-server")
HIVE_PORT = int(os.getenv("HIVE_PORT", "10000"))


def execute_query(cursor, sql: str):
    cursor.execute(sql)
    return cursor.fetchall()


def execute_scalar(cursor, sql: str):
    cursor.execute(sql)
    row = cursor.fetchone()
    return row[0] if row else None


def validate_gold() -> None:
    """Validation qualité données Gold."""
    try:
        logger.info("🔹 Démarrage validation qualité Gold")

        conn = connect(host=HIVE_HOST, port=HIVE_PORT, database="default")
        cursor = conn.cursor()

        required_tables = [
            "dim_temps",
            "dim_diagnostic",
            "dim_patient",
            "fait_hospitalisation",
        ]

        # Vérifier que les tables existent
        existing_tables = {row[0] for row in execute_query(cursor, "SHOW TABLES IN gold")}
        missing = [t for t in required_tables if t not in existing_tables]
        if missing:
            raise Exception(f"Tables manquantes dans gold: {', '.join(missing)}")

        # Nombre de lignes par table
        for table in required_tables:
            count = execute_scalar(cursor, f"SELECT COUNT(*) FROM gold.{table}")
            logger.info(f"✓ gold.{table}: {count} lignes")
            if count == 0:
                raise Exception(f"gold.{table} est vide")

        # Null checks
        null_checks = {
            "gold.dim_temps": ["id_temps", "date_complete", "annee"],
            "gold.dim_diagnostic": ["code_diag", "libelle"],
            "gold.dim_patient": ["id_patient"],
            "gold.fait_hospitalisation": ["id_temps", "id_patient"],
        }
        for table, columns in null_checks.items():
            for column in columns:
                null_count = execute_scalar(
                    cursor,
                    f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
                )
                if null_count is None:
                    raise Exception(f"Impossible de vérifier les nulls pour {table}.{column}")
                if null_count > 0:
                    raise Exception(f"{null_count} valeurs NULL trouvées dans {table}.{column}")

        # Duplicate checks
        duplicate_checks = {
            "gold.dim_temps": ["id_temps"],
            "gold.dim_diagnostic": ["code_diag"],
            "gold.dim_patient": ["id_patient"],
            "gold.fait_hospitalisation": ["id_fait_hospitalisation"],
        }
        for table, keys in duplicate_checks.items():
            key_expr = ", ".join(keys)
            dup_count = execute_scalar(
                cursor,
                f"SELECT SUM(cnt - 1) FROM (SELECT {key_expr}, COUNT(*) AS cnt FROM {table} GROUP BY {key_expr} HAVING COUNT(*) > 1) dup"
            )
            if dup_count is None:
                dup_count = 0
            if dup_count > 0:
                raise Exception(f"{dup_count} doublons détectés dans {table} sur {key_expr}")

        # Range checks
        range_checks = [
            (
                "gold.dim_temps",
                "annee",
                "SELECT MIN(annee), MAX(annee) FROM gold.dim_temps",
                lambda min_v, max_v: (min_v is not None and min_v >= 1900 and max_v <= 2100),
                "annee doit être entre 1900 et 2100",
            ),
            (
                "gold.dim_patient",
                "age",
                "SELECT MIN(age), MAX(age) FROM gold.dim_patient",
                lambda min_v, max_v: (min_v is None or (min_v >= 0 and max_v <= 150)),
                "age doit être entre 0 et 150 ou NULL",
            ),
            (
                "gold.fait_hospitalisation",
                "nb_hospitalisation",
                "SELECT MIN(nb_hospitalisation), MAX(nb_hospitalisation) FROM gold.fait_hospitalisation",
                lambda min_v, max_v: (min_v is None or (min_v >= 0 and max_v <= 9999)),
                "nb_hospitalisation doit être >= 0 ou NULL",
            ),
        ]

        for table, column, sql, validator, message in range_checks:
            row = execute_query(cursor, sql)
            if not row or row[0] is None:
                continue
            min_value, max_value = row[0]
            if not validator(min_value, max_value):
                raise Exception(f"Validation range échouée pour {table}.{column}: {message} (min={min_value}, max={max_value})")
            logger.info(f"✓ {table}.{column} range ok (min={min_value}, max={max_value})")

        cursor.close()
        conn.close()

        logger.info("✅ Validation réussie")

    except Exception as e:
        logger.error(f"❌ Erreur validation: {str(e)}")
        raise


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    validate_gold()
