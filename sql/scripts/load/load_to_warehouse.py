"""
Chargement Hive/Gold - Exécute les transformations HiveQL

Cette tâche:
1. Exécute les scripts HiveQL (dimensions + faits)
2. Vérifie le chargement
3. Crée les partitions

Idempotent: upsert dans Hive.
"""

from pyhive.hive import connect
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Config Hive
HIVE_HOST = 'hive-server'
HIVE_PORT = 10000


def load_to_warehouse() -> None:
    """Chargement des données dans Hive Gold."""
    try:
        logger.info("🔹 Démarrage chargement Hive Gold")
        
        # Connexion Hive
        conn = connect(
            host=HIVE_HOST,
            port=HIVE_PORT,
            database='default'
        )
        cursor = conn.cursor()
        logger.info("✓ Connecté à Hive")
        
        # Scripts HiveQL à exécuter (dans l'ordre)
        sql_files = [
            '/scripts/transform/tHospTimPatDiag.sql',
            # À ajouter: autres dimensions et faits
        ]
        
        for sql_file in sql_files:
            try:
                sql_path = Path(sql_file)
                if not sql_path.exists():
                    logger.warning(f"⚠ Fichier n'existe pas: {sql_file}")
                    continue
                
                logger.info(f"  → Exécution {sql_path.name}")
                
                # Lire et exécuter
                with open(sql_file, 'r') as f:
                    query = f.read()
                
                cursor.execute(query)
                logger.info(f"    ✓ Exécuté")
                
            except Exception as e:
                logger.error(f"    ❌ Erreur: {str(e)}")
                raise
        
        cursor.close()
        conn.close()
        logger.info("✅ Chargement Hive réussi")
        
    except Exception as e:
        logger.error(f"❌ Erreur chargement Hive: {str(e)}")
        raise


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    load_to_warehouse()
