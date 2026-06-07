"""
Extraction des donnees geographie vers la zone Bronze.
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


def _extract_region(text: str | None) -> str | None:
    if text is None:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 2:
        return None
    return digits[:2]


def _from_raw_geographie() -> list[tuple[str, str, str]]:
    files = (
        sorted(RAW_DIR.glob("*geograph*.csv"))
        + sorted(RAW_DIR.glob("*region*.csv"))
        + sorted(BRONZE_DIR.glob("*geograph*.csv"))
        + sorted(BRONZE_DIR.glob("*region*.csv"))
    )
    if not files:
        return []

    frame = pd.read_csv(files[0], dtype=str, sep=None, engine="python", on_bad_lines="skip")
    if frame.empty:
        return []

    col_map = {_normalize_col(col): col for col in frame.columns}
    code_col = _find_column(col_map, ["code_region", "region", "code"])
    label_col = _find_column(col_map, ["libelle_region", "nom_region", "region_label"])
    country_col = _find_column(col_map, ["pays", "country"])

    rows: list[tuple[str, str, str]] = []
    for _, row in frame.iterrows():
        code = _extract_region(str(row[code_col])) if code_col else None
        if code is None:
            continue
        label = str(row[label_col]).strip() if label_col and pd.notna(row[label_col]) else f"Region_{code}"
        country = str(row[country_col]).strip() if country_col and pd.notna(row[country_col]) else "FRANCE"
        rows.append((code, label, country))
    return rows


def _from_bronze_fallback() -> list[tuple[str, str, str]]:
    rows: set[tuple[str, str, str]] = set()

    deces_file = BRONZE_DIR / "deces_raw.csv"
    if deces_file.exists():
        frame = pd.read_csv(deces_file, dtype=str)
        if "code_region" in frame.columns:
            for code in frame["code_region"].dropna().astype(str):
                code2 = _extract_region(code)
                if code2:
                    rows.add((code2, f"Region_{code2}", "FRANCE"))

    satisfaction_file = BRONZE_DIR / "satisfaction_raw.csv"
    if satisfaction_file.exists():
        frame = pd.read_csv(satisfaction_file, dtype=str)
        if "code_region" in frame.columns:
            for code in frame["code_region"].dropna().astype(str):
                code2 = _extract_region(code)
                if code2:
                    rows.add((code2, f"Region_{code2}", "FRANCE"))

    return sorted(rows, key=lambda item: item[0])


def extract_geographie() -> None:
    logger.info("Demarrage extraction geographie")

    rows = _from_raw_geographie()
    if not rows:
        rows = _from_bronze_fallback()

    if not rows:
        raise ValueError("Aucune donnee geographie exploitable")

    unique_rows = sorted(set(rows), key=lambda item: item[0])
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    output = BRONZE_DIR / "geographie_raw.csv"
    pd.DataFrame(unique_rows, columns=["code_region", "libelle_region", "pays"]).to_csv(output, index=False)

    logger.info("Extraction geographie terminee avec %s lignes vers %s", len(unique_rows), output.name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extract_geographie()
