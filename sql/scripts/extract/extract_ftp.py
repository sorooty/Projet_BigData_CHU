"""
Extraction FTP - Sources externes distantes.

Cette tache:
1. Se connecte a un serveur FTP/FTPS
2. Telecharge les fichiers cibles dans data/raw
3. Laisse extract_csv traiter les CSV en bronze

Execution idempotente.
"""

import fnmatch
import logging
import os
from ftplib import FTP, FTP_TLS
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
RAW_DIR = DATA_ROOT / "raw"

FTP_ENABLED = os.getenv("FTP_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
FTP_USE_TLS = os.getenv("FTP_USE_TLS", "false").strip().lower() in {"1", "true", "yes", "on"}
FTP_HOST = os.getenv("FTP_HOST", "").strip()
FTP_PORT = int(os.getenv("FTP_PORT", "21"))
FTP_USER = os.getenv("FTP_USER", "").strip()
FTP_PASSWORD = os.getenv("FTP_PASSWORD", "").strip()
FTP_REMOTE_DIR = os.getenv("FTP_REMOTE_DIR", "").strip() or "/"
FTP_FILE_PATTERN = os.getenv("FTP_FILE_PATTERN", "*.csv").strip() or "*.csv"
FTP_TIMEOUT = int(os.getenv("FTP_TIMEOUT", "60"))


def _get_ftp_client():
    client_cls = FTP_TLS if FTP_USE_TLS else FTP
    client = client_cls()
    client.connect(host=FTP_HOST, port=FTP_PORT, timeout=FTP_TIMEOUT)
    client.login(user=FTP_USER, passwd=FTP_PASSWORD)
    if FTP_USE_TLS:
        client.prot_p()
    return client


def extract_ftp() -> None:
    """Telecharge les fichiers FTP dans data/raw."""
    if not FTP_ENABLED:
        logger.info("FTP desactive (FTP_ENABLED=false), extraction ignoree.")
        return

    if not FTP_HOST:
        raise ValueError("FTP_HOST est requis quand FTP_ENABLED=true")
    if not FTP_USER:
        raise ValueError("FTP_USER est requis quand FTP_ENABLED=true")
    if not FTP_PASSWORD:
        raise ValueError("FTP_PASSWORD est requis quand FTP_ENABLED=true")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Demarrage extraction FTP")
    with _get_ftp_client() as ftp:
        ftp.cwd(FTP_REMOTE_DIR)
        remote_files = ftp.nlst()
        selected_files = sorted(
            name for name in remote_files
            if fnmatch.fnmatch(name, FTP_FILE_PATTERN)
        )

        if not selected_files:
            raise FileNotFoundError(
                f"Aucun fichier FTP correspondant a {FTP_FILE_PATTERN} dans {FTP_REMOTE_DIR}"
            )

        logger.info("Trouve %s fichiers FTP", len(selected_files))
        for remote_name in selected_files:
            target = RAW_DIR / f"ftp_{Path(remote_name).name}"
            logger.info("Telechargement %s", remote_name)
            with target.open("wb") as output_stream:
                ftp.retrbinary(f"RETR {remote_name}", output_stream.write)
            logger.info("Sauvegarde en %s", target.name)

    logger.info("Extraction FTP reussie")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extract_ftp()
