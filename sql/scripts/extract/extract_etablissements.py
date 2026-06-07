"""
Extraction des etablissements vers la zone Bronze.
"""

import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data"))
RAW_DIR = DATA_ROOT / "raw"
BRONZE_DIR = DATA_ROOT / "bronze"


def _normalize_col(name: str) -> str:
    return "".join(ch for ch in str(name).strip().lower() if ch.isalnum())


def _find_column(col_map: dict[str, str], aliases: list[str]) -> str | None:
    for alias in aliases:
        key = _normalize_col(alias)
        if key in col_map:
            return col_map[key]
    return None


def _find_source() -> Path:
    candidates = (
        sorted(RAW_DIR.glob("*etablissement*.csv"))
        + sorted(RAW_DIR.glob("*etablissements*.csv"))
        + sorted(BRONZE_DIR.glob("*etablissement*.csv"))
        + sorted(BRONZE_DIR.glob("*etablissements*.csv"))
    )
    if not candidates:
        raise FileNotFoundError(f"Aucun CSV etablissements trouve dans {RAW_DIR} ou {BRONZE_DIR}")
    return candidates[0]


def _normalize_finess(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return None
    normalized = digits.lstrip("0")
    return normalized or "0"


def _extract_region_from_postal(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) < 2:
        return None
    return digits[:2]


def extract_etablissements() -> None:
    source = _find_source()
    logger.info("Demarrage extraction etablissements depuis %s", source.name)

    frame = pd.read_csv(source, dtype=str, sep=None, engine="python", on_bad_lines="skip")
    if frame.empty:
        raise ValueError(f"Fichier etablissements vide: {source}")

    col_map = {_normalize_col(col): col for col in frame.columns}
    finess_col = _find_column(
        col_map,
        [
            "finess",
            "finess_site",
            "finessetablissementjuridique",
            "id_etablissement",
            "etablissement",
        ],
    )
    finess_alt_col = _find_column(
        col_map,
        [
            "finess_site",
            "finessetablissementjuridique",
            "finess",
        ],
    )
    nom_col = _find_column(
        col_map,
        [
            "nom",
            "nom_etablissement",
            "raisonsocialesite",
            "raison_sociale",
            "enseignecommercialesite",
        ],
    )
    code_region_col = _find_column(col_map, ["code_region", "region", "region_code"])
    code_postal_col = _find_column(col_map, ["code_postal", "codepostal"])

    rows: list[tuple[str, str, str]] = []
    for _, row in frame.iterrows():
        raw_finess = str(row[finess_col]).strip() if finess_col and pd.notna(row[finess_col]) else None
        if (raw_finess is None or raw_finess == "") and finess_alt_col and pd.notna(row[finess_alt_col]):
            raw_finess = str(row[finess_alt_col]).strip()
        finess = _normalize_finess(raw_finess)
        if not finess:
            continue
        nom = str(row[nom_col]).strip() if nom_col and pd.notna(row[nom_col]) else None
        code_region = str(row[code_region_col]).strip() if code_region_col and pd.notna(row[code_region_col]) else None
        if not code_region and code_postal_col and pd.notna(row[code_postal_col]):
            code_region = _extract_region_from_postal(str(row[code_postal_col]).strip())
        rows.append((finess, nom or "", code_region or ""))

    if not rows:
        raise ValueError("Aucune ligne etablissements exploitable apres normalisation")

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    output = BRONZE_DIR / "etablissements_raw.csv"
    pd.DataFrame(rows, columns=["finess", "nom", "code_region"]).to_csv(output, index=False)

    logger.info("Extraction etablissements terminee avec %s lignes vers %s", len(rows), output.name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extract_etablissements()
