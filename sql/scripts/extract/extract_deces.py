"""
Extraction des donnees deces vers la zone Bronze.
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


def _to_text_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_region(code_lieu: str | None) -> str | None:
    if code_lieu is None:
        return None
    digits = "".join(ch for ch in code_lieu if ch.isdigit())
    if len(digits) < 2:
        return None
    return digits[:2]


def _find_deces_file() -> Path:
    candidates = (
        sorted(RAW_DIR.glob("*deces*.csv"))
        + sorted(RAW_DIR.glob("*DECES*.csv"))
        + sorted(BRONZE_DIR.glob("*deces*.csv"))
        + sorted(BRONZE_DIR.glob("*DECES*.csv"))
    )
    if not candidates:
        raise FileNotFoundError(f"Aucun CSV deces trouve dans {RAW_DIR} ou {BRONZE_DIR}")
    return candidates[0]


def extract_deces() -> None:
    source = _find_deces_file()
    logger.info("Demarrage extraction deces depuis %s", source.name)

    df = pd.read_csv(source, dtype=str, sep=None, engine="python", on_bad_lines="skip")
    if df.empty:
        raise ValueError(f"Fichier deces vide: {source}")

    col_map = {_normalize_col(col): col for col in df.columns}
    date_col = _find_column(col_map, ["date_deces", "date", "datemort", "annee"])
    patient_col = _find_column(col_map, ["id_patient", "patient", "num_patient"])
    code_lieu_col = _find_column(col_map, ["code_lieu_deces", "code_lieu", "code_region", "region"])
    nb_deces_col = _find_column(col_map, ["nb_deces", "nombre_deces"])

    rows: list[tuple[str, str, str, int]] = []
    for _, row in df.iterrows():
        date_deces = _to_text_or_none(row[date_col]) if date_col else None
        if date_deces is None:
            continue
        date_deces = date_deces[:10]

        patient = _to_text_or_none(row[patient_col]) if patient_col else None
        if patient is None:
            patient = "UNKNOWN"

        code_lieu = _to_text_or_none(row[code_lieu_col]) if code_lieu_col else None
        code_region = _extract_region(code_lieu)
        if code_region is None:
            continue

        nb_deces = 1
        if nb_deces_col:
            raw_nb = _to_text_or_none(row[nb_deces_col])
            if raw_nb:
                try:
                    nb_deces = int(float(raw_nb))
                except ValueError:
                    nb_deces = 1

        rows.append((date_deces, patient, code_region, nb_deces))

    if not rows:
        raise ValueError("Aucune ligne deces exploitable apres normalisation")

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    output = BRONZE_DIR / "deces_raw.csv"
    pd.DataFrame(
        rows,
        columns=["date_deces", "id_patient", "code_region", "nb_deces"],
    ).to_csv(output, index=False)

    logger.info("Extraction deces terminee avec %s lignes vers %s", len(rows), output.name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extract_deces()
