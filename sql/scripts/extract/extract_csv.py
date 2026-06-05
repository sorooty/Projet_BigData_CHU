"""
Extraction CSV - Sources externes.

Cette tache:
1. Recupere les CSV sources du dossier Raw du conteneur Airflow
2. Nettoie les colonnes totalement vides
3. Sauvegarde en Bronze

Execution idempotente.
"""

import os
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
RAW_DIR = DATA_ROOT / "raw"
BRONZE_DIR = DATA_ROOT / "bronze"


def extract_csv() -> None:
    """Extraction CSV sources."""
    try:
        logger.info("Demarrage extraction CSV sources")
        
        BRONZE_DIR.mkdir(parents=True, exist_ok=True)

        if not RAW_DIR.exists():
            raise FileNotFoundError(f"Dossier source introuvable: {RAW_DIR}")

        # Traiter chaque CSV
        csv_files = sorted(RAW_DIR.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"Aucun CSV trouve dans {RAW_DIR}")

        logger.info(f"Trouve {len(csv_files)} fichiers CSV")
        
        for csv_file in csv_files:
            try:
                logger.info(f"Traitement {csv_file.name}")
                
                # Lire CSV
                df = pd.read_csv(csv_file)
                logger.info(f"Charge {len(df)} lignes")
                
                # Validation basique: drop colonnes entièrement nulles
                initial_cols = len(df.columns)
                df = df.dropna(axis=1, how='all')
                if len(df.columns) < initial_cols:
                    logger.warning(f"Supprime {initial_cols - len(df.columns)} colonnes nulles")
                
                # Sauvegarder en Bronze
                output_file = BRONZE_DIR / f"{csv_file.stem}_raw.csv"
                df.to_csv(output_file, index=False)
                logger.info(f"Sauvegarde en {output_file.name}")
                
            except Exception as e:
                logger.error(f"Erreur traitement {csv_file.name}: {str(e)}")
                raise
        
        logger.info("Extraction CSV reussie")
        
    except Exception as e:
        logger.error(f"Erreur extraction CSV: {str(e)}")
        raise


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    extract_csv()
