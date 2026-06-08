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


# Mapping code département (2 chiffres) -> code région INSEE (post-2016)
_DEP_TO_REGION: dict[str, str] = {
    "01": "84", "02": "32", "03": "84", "04": "93", "05": "93",
    "06": "93", "07": "84", "08": "44", "09": "76", "10": "44",
    "11": "76", "12": "76", "13": "93", "14": "28", "15": "84",
    "16": "75", "17": "75", "18": "24", "19": "75", "21": "27",
    "22": "53", "23": "75", "24": "75", "25": "27", "26": "84",
    "27": "28", "28": "24", "29": "53", "30": "76", "31": "76",
    "32": "76", "33": "75", "34": "76", "35": "53", "36": "24",
    "37": "24", "38": "84", "39": "27", "40": "75", "41": "24",
    "42": "84", "43": "84", "44": "52", "45": "24", "46": "76",
    "47": "75", "48": "76", "49": "52", "50": "28", "51": "44",
    "52": "44", "53": "52", "54": "44", "55": "44", "56": "53",
    "57": "44", "58": "27", "59": "32", "60": "32", "61": "28",
    "62": "32", "63": "84", "64": "75", "65": "76", "66": "76",
    "67": "44", "68": "44", "69": "84", "70": "27", "71": "27",
    "72": "52", "73": "84", "74": "84", "75": "11", "76": "28",
    "77": "11", "78": "11", "79": "75", "80": "32", "81": "76",
    "82": "76", "83": "93", "84": "93", "85": "52", "86": "75",
    "87": "75", "88": "44", "89": "27", "90": "27", "91": "11",
    "92": "11", "93": "11", "94": "11", "95": "11",
    # Outre-mer
    "971": "01", "972": "02", "973": "03", "974": "04", "976": "06",
}


def _extract_region(code_lieu: str | None) -> str | None:
    """
    Convertit un code commune/département en code région INSEE (post-2016).
    Le code_lieu_deces est un code INSEE commune sur 5 chiffres (ex: 02691).
    Les 2 premiers chiffres = département, mappé vers la région.
    """
    if code_lieu is None:
        return None
    digits = "".join(ch for ch in code_lieu if ch.isdigit())
    if len(digits) < 2:
        return None
    # Essai sur 3 chiffres (outre-mer 97x) puis 2 chiffres
    dep3 = digits[:3]
    if dep3 in _DEP_TO_REGION:
        return _DEP_TO_REGION[dep3]
    dep2 = digits[:2]
    return _DEP_TO_REGION.get(dep2)


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

    # Déduire les noms de colonnes sur les 2 premières lignes (tête du fichier)
    header_df = pd.read_csv(source, sep=",", nrows=2, dtype=str)
    col_map       = {_normalize_col(col): col for col in header_df.columns}
    date_col      = _find_column(col_map, ["date_deces", "date", "datemort", "annee"])
    patient_col   = _find_column(col_map, ["id_patient", "patient", "num_patient"])
    code_lieu_col = _find_column(col_map, ["code_lieu_deces", "code_lieu", "code_region", "region"])
    nb_deces_col  = _find_column(col_map, ["nb_deces", "nombre_deces"])

    if date_col is None:
        raise ValueError(f"Colonne date_deces introuvable. Colonnes : {list(header_df.columns)}")

    # usecols : ne lire que les colonnes utiles → mémoire ÷3-5
    useful_cols = [c for c in [date_col, code_lieu_col, patient_col, nb_deces_col] if c]

    # #region agent log
    import json, time as _t
    with open("/opt/airflow/data/debug-bddb4f.log", "a") as _f:
        _f.write(json.dumps({"sessionId":"bddb4f","timestamp":int(_t.time()*1000),"location":"extract_deces.py:load","message":"chunked reader started","data":{"date_col":date_col,"code_lieu_col":code_lieu_col,"useful_cols":useful_cols},"hypothesisId":"H-deces","runId":"post-fix"}) + "\n")
    # #endregion

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    output = BRONZE_DIR / "deces_raw.csv"
    total_rows = 0
    write_header = True

    # Lecture par chunks de 500k lignes — itération SANS list() pour ne jamais
    # charger plus d'un chunk en RAM simultanément
    CHUNK_SIZE = 500_000
    for i, chunk in enumerate(pd.read_csv(
        source, dtype=str, sep=",", on_bad_lines="skip",
        usecols=useful_cols, chunksize=CHUNK_SIZE,
    )):
        # --- Date : tronquer à 10 chars, supprimer nulls ---
        chunk["_date"] = chunk[date_col].astype(str).str.strip().str[:10]
        chunk = chunk[chunk["_date"].str.len() == 10]
        if chunk.empty:
            continue

        # --- Région : mapping vectorisé ---
        if code_lieu_col:
            digits = chunk[code_lieu_col].astype(str).str.strip().str.replace(r"\D", "", regex=True)
            chunk["_region"] = digits.str[:3].map(_DEP_TO_REGION).fillna(digits.str[:2].map(_DEP_TO_REGION))
            chunk = chunk[chunk["_region"].notna()]
        else:
            continue  # pas de colonne lieu → lignes inexploitables

        chunk["_patient"] = "UNKNOWN"
        chunk["_nb"] = 1

        chunk[["_date", "_patient", "_region", "_nb"]].rename(columns={
            "_date": "date_deces", "_patient": "id_patient",
            "_region": "code_region", "_nb": "nb_deces",
        }).to_csv(output, index=False, mode="w" if write_header else "a", header=write_header)
        total_rows += len(chunk)
        write_header = False

        if i % 5 == 0:
            logger.info("Chunk %s OK, %s lignes totales", i, total_rows)

    if total_rows == 0:
        raise ValueError("Aucune ligne deces exploitable apres normalisation")

    logger.info("Extraction deces terminee avec %s lignes vers %s", total_rows, output.name)
    # #region agent log
    with open("/opt/airflow/data/debug-bddb4f.log", "a") as _f:
        _f.write(json.dumps({"sessionId":"bddb4f","timestamp":int(_t.time()*1000),"location":"extract_deces.py:done","message":"extraction complete","data":{"rows_out":total_rows},"hypothesisId":"H-deces","runId":"post-fix"}) + "\n")
    # #endregion


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extract_deces()
