"""
Extraction CSV - Sources externes (établissements, satisfaction, etc)

Cette tâche:
1. Récupère les CSV sources de /data/raw/
2. Valide les colonnes
3. Sauvegarde en Bronze

Idempotent: peut s'exécuter plusieurs fois.
"""

import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def extract_csv() -> None:
    """Extraction CSV sources."""
    try:
        logger.info("🔹 Démarrage extraction CSV sources")
        
        # Dossiers
        raw_dir = Path('/data/raw')
        bronze_dir = Path('/data/bronze')
        bronze_dir.mkdir(parents=True, exist_ok=True)
        
        if not raw_dir.exists():
            logger.warning(f"Dossier {raw_dir} n'existe pas")
            return
        
        # Traiter chaque CSV
        csv_files = list(raw_dir.glob('*.csv'))
        logger.info(f"🔹 Trouvé {len(csv_files)} fichiers CSV")
        
        for csv_file in csv_files:
            try:
                logger.info(f"  → Traitement {csv_file.name}")
                
                # Lire CSV
                df = pd.read_csv(csv_file)
                logger.info(f"    ✓ Chargé {len(df)} lignes")
                
                # Validation basique: drop colonnes entièrement nulles
                initial_cols = len(df.columns)
                df = df.dropna(axis=1, how='all')
                if len(df.columns) < initial_cols:
                    logger.warning(f"    ⚠ Supprimé {initial_cols - len(df.columns)} colonnes nulles")
                
                # Sauvegarder en Bronze
                output_file = bronze_dir / f"{csv_file.stem}_raw.csv"
                df.to_csv(output_file, index=False)
                logger.info(f"    ✓ Sauvegardé en {output_file.name}")
                
            except Exception as e:
                logger.error(f"    ❌ Erreur traitement {csv_file.name}: {str(e)}")
                raise
        
        logger.info("✅ Extraction CSV réussie")
        
    except Exception as e:
        logger.error(f"❌ Erreur extraction CSV: {str(e)}")
        raise


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    extract_csv()
