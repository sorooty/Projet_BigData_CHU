"""
Extraction des donnees satisfaction vers la zone Bronze.
"""

import logging
import os
import re
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


def _to_float_or_none(value: object) -> float | None:
    text = _to_text_or_none(value)
    if text is None:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def _find_satisfaction_files() -> list[Path]:
    files = sorted(RAW_DIR.glob("*satisfaction*.csv")) + sorted(RAW_DIR.glob("*Satisfaction*.csv"))
    if not files:
        raise FileNotFoundError(f"Aucun CSV satisfaction trouve dans {RAW_DIR}")
    return files


def _year_from_filename(path: Path) -> int:
    match = re.search(r"(20\d{2})", path.name)
    if match:
        return int(match.group(1))
    return 2024


def extract_satisfaction() -> None:
    source_files = _find_satisfaction_files()
    logger.info("Demarrage extraction satisfaction (%s fichiers)", len(source_files))

    rows: list[tuple[str, str, str, float]] = []
    for source in source_files:
        frame = pd.read_csv(source, dtype=str, sep=None, engine="python", on_bad_lines="skip")
        if frame.empty:
            continue

        col_map = {_normalize_col(col): col for col in frame.columns}
        finess_col = _find_column(col_map, ["finess", "id_etablissement", "etablissement"])
        region_col = _find_column(col_map, ["code_region", "region", "code_lieu_deces"])
        date_col = _find_column(col_map, ["date_satisfaction", "date", "annee"])
        score_col = _find_column(
            col_map,
            ["score_global", "score", "tdacetbt", "trdcetbt", "deccetbt", "dtncetbt", "tdpcetbt", "trecetbt"],
        )

        for _, row in frame.iterrows():
            finess = _to_text_or_none(row[finess_col]) if finess_col else None
            code_region = _to_text_or_none(row[region_col]) if region_col else None
            if code_region and len(code_region) > 2:
                code_region = "".join(ch for ch in code_region if ch.isdigit())[:2] or code_region[:2]

            score = _to_float_or_none(row[score_col]) if score_col else None
            if finess is None or code_region is None or score is None:
                continue

            date_value = _to_text_or_none(row[date_col]) if date_col else None
            if date_value is None:
                date_value = f"{_year_from_filename(source)}-01-01"
            else:
                date_value = date_value[:10]

            rows.append((date_value, finess, code_region, score))

    if not rows:
        raise ValueError("Aucune ligne satisfaction exploitable apres normalisation")

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    output = BRONZE_DIR / "satisfaction_raw.csv"
    pd.DataFrame(
        rows,
        columns=["date_satisfaction", "finess", "code_region", "score_global"],
    ).to_csv(output, index=False)

    logger.info("Extraction satisfaction terminee avec %s lignes vers %s", len(rows), output.name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extract_satisfaction()
