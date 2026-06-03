"""
Extraction PostgreSQL - Consultations et données sources

Cette tâche:
1. Se connecte à PostgreSQL
2. Récupère les consultations depuis hier
3. Sauvegarde en CSV dans /data/bronze/

Idempotent: peut s'exécuter plusieurs fois sans casse.
"""

import psycopg2
import pandas as pd
from pathlib import Path
import sys
import logging

# Logger
logger = logging.getLogger(__name__)

# Config PostgreSQL (depuis env)
PG_HOST = 'postgres'  # ou from os.getenv('POSTGRES_HOST')
PG_USER = 'admin'     # ou from os.getenv('POSTGRES_USER')
PG_PASSWORD = 'admin' # ou from os.getenv('POSTGRES_PASSWORD')
PG_DATABASE = 'chu'   # ou from os.getenv('POSTGRES_DB')


def extract_consultations() -> None:
    """Extraction principale."""
    try:
        logger.info("🔹 Démarrage extraction PostgreSQL consultations")
        
        # Connexion PostgreSQL
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        logger.info("✓ Connecté à PostgreSQL")
        
        # Requête (à adapter au schéma réel)
        query = """
            SELECT 
                id_consultation,
                id_patient,
                date_consultation,
                diagnostic,
                id_etablissement,
                montant
            FROM consultation
            WHERE date_consultation >= CURRENT_DATE - INTERVAL '1 day'
            ORDER BY date_consultation DESC
        """
        
        df = pd.read_sql(query, conn)
        logger.info(f"✓ Récupéré {len(df)} consultations")
        
        # Créer dossier Bronze si n'existe pas
        output_dir = Path('/data/bronze')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder en CSV
        output_file = output_dir / 'consultations_raw.csv'
        df.to_csv(output_file, index=False)
        logger.info(f"✓ Sauvegardé en {output_file}")
        
        conn.close()
        logger.info("✅ Extraction PostgreSQL réussie")
        
    except Exception as e:
        logger.error(f"❌ Erreur extraction PostgreSQL: {str(e)}")
        raise


if __name__ == '__main__':
    # Exécution standalone: python extract_postgres.py
    logging.basicConfig(level=logging.INFO)
    extract_consultations()
