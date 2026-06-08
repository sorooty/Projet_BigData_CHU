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


# Mapping nom de région (anciens et nouveaux) -> code INSEE région (post-2016)
_REGION_NAME_TO_CODE: dict[str, str] = {
    # Nouvelles régions
    "hautsdefrance": "32",
    "normandie": "28",
    "iledefrance": "11",
    "centrevaldeloire": "24",
    "grandest": "44",
    "bourgognefranchecomte": "27",
    "paysdelaloire": "52",
    "bretagne": "53",
    "nouvelleaquitaine": "75",
    "auvergnerhonealpes": "84",
    "occitanie": "76",
    "provencealpescotedazur": "93",
    "paca": "93",
    "corse": "94",
    # Anciennes régions (pré-2016)
    "nordpasdecalais": "32",
    "nordpasdecalaispicardie": "32",
    "picardie": "32",
    "hautenormandie": "28",
    "bassenormandie": "28",
    "centre": "24",
    "champagneardenne": "44",
    "alsace": "44",
    "lorraine": "44",
    "bourgogne": "27",
    "franchecomte": "27",
    "poitoucharentes": "75",
    "limousin": "75",
    "aquitaine": "75",
    "auvergne": "84",
    "rhonealpes": "84",
    "languedocroussillon": "76",
    "midipyrenees": "76",
    # Outre-mer
    "guadeloupe": "01",
    "martinique": "02",
    "guyane": "03",
    "lareunion": "04",
    "reunion": "04",
    "mayotte": "06",
}


def _normalize_region_name(text: str) -> str:
    """Retire accents, espaces, tirets, casse pour lookup uniforme."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return "".join(ch.lower() for ch in ascii_text if ch.isalpha())


def _region_name_to_code(name: str | None) -> str | None:
    if not name:
        return None
    key = _normalize_region_name(name)
    return _REGION_NAME_TO_CODE.get(key)


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
    files = (
        sorted(RAW_DIR.glob("*satisfaction*.csv"))
        + sorted(RAW_DIR.glob("*Satisfaction*.csv"))
        + sorted(BRONZE_DIR.glob("*satisfaction*.csv"))
        + sorted(BRONZE_DIR.glob("*Satisfaction*.csv"))
    )
    if not files:
        raise FileNotFoundError(f"Aucun CSV satisfaction trouve dans {RAW_DIR} ou {BRONZE_DIR}")
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
        frame = pd.read_csv(source, dtype=str, sep=None, engine="python", on_bad_lines="skip", encoding="latin-1")
        # #region agent log
        import json, time as _t
        with open("/opt/airflow/data/debug-bddb4f.log", "a") as _f:
            _f.write(json.dumps({"sessionId":"bddb4f","timestamp":int(_t.time()*1000),"location":"extract_satisfaction.py:read","message":"file read ok","data":{"file":str(source.name),"rows":len(frame)},"hypothesisId":"H-sat","runId":"post-fix"}) + "\n")
        # #endregion
        if frame.empty:
            continue

        col_map = {_normalize_col(col): col for col in frame.columns}
        finess_col = _find_column(
            col_map,
            ["finess", "finess_site", "id_etablissement", "etablissement", "finessetablissementjuridique"],
        )
        region_code_col = _find_column(col_map, ["code_region", "region_code", "coderegion"])
        region_name_col = _find_column(col_map, ["libelle_region", "libelleregion", "nom_region", "region"])
        date_col = _find_column(col_map, ["date_satisfaction", "date", "annee"])
        score_col = _find_column(
            col_map,
            ["score_global", "score", "tdacetbt", "trdcetbt", "deccetbt", "dtncetbt", "tdpcetbt", "trecetbt"],
        )

        for _, row in frame.iterrows():
            finess = _to_text_or_none(row[finess_col]) if finess_col else None
            if finess:
                digits = "".join(ch for ch in finess if ch.isdigit())
                finess = digits.lstrip("0") or "0"

            # Priorité : colonne code_region numérique, sinon libelle_region -> mapping
            code_region = _to_text_or_none(row[region_code_col]) if region_code_col else None
            if code_region and len(code_region) > 3:
                # Valeur texte dans une colonne code_region -> traiter comme nom
                code_region = _region_name_to_code(code_region)
            elif not code_region and region_name_col:
                region_name = _to_text_or_none(row[region_name_col])
                code_region = _region_name_to_code(region_name)

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
