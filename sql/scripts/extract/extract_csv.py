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
import shutil

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
RAW_DIR = DATA_ROOT / "raw"
BRONZE_DIR = DATA_ROOT / "bronze"
MAX_PARSE_SIZE_MB = int(os.getenv("CSV_MAX_PARSE_SIZE_MB", "300"))


def _safe_copy_to_bronze(source: Path, destination: Path) -> None:
    shutil.copy2(source, destination)
    logger.warning(
        "Fichier trop volumineux pour nettoyage memoire-safe, copie brute: %s",
        source.name,
    )


def _clean_csv_in_chunks(source: Path, destination: Path) -> None:
    chunk_size = int(os.getenv("CSV_CHUNK_SIZE", "100000"))
    read_options = {
        "dtype": str,
        "chunksize": chunk_size,
        "sep": None,
        "engine": "python",
        "on_bad_lines": "skip",
        "encoding": "latin1",
    }

    # Pass 1: colonnes non vides
    non_empty = None
    columns = None
    for chunk in pd.read_csv(source, **read_options):
        if columns is None:
            columns = list(chunk.columns)
            non_empty = {col: False for col in columns}

        for col in columns:
            values = chunk[col]
            if values.notna().any() and values.astype(str).str.strip().ne("").any():
                non_empty[col] = True

    if columns is None:
        raise ValueError(f"Fichier CSV vide: {source}")

    selected_columns = [col for col in columns if non_empty[col]]
    removed_columns = len(columns) - len(selected_columns)

    # Pass 2: ecriture nettoyee
    write_header = True
    for chunk in pd.read_csv(source, **read_options):
        chunk[selected_columns].to_csv(
            destination,
            mode="w" if write_header else "a",
            index=False,
            header=write_header,
        )
        write_header = False

    if removed_columns > 0:
        logger.warning("Supprime %s colonnes nulles", removed_columns)


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

                # Sauvegarder en Bronze
                output_file = BRONZE_DIR / f"{csv_file.stem}_raw.csv"
                file_size_mb = csv_file.stat().st_size / (1024 * 1024)

                if file_size_mb > MAX_PARSE_SIZE_MB:
                    _safe_copy_to_bronze(csv_file, output_file)
                else:
                    _clean_csv_in_chunks(csv_file, output_file)

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
