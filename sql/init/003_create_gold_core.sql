-- ============================================================
-- DIMENSIONS (A CHANGER - OMAR et ABDOULAYE) (partagées entre plusieurs tables de faits)
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.dim_temps (
    id_temps     INT PRIMARY KEY,
    date_complete DATE NOT NULL,
    annee        INT  NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.dim_patient (
    id_patient   TEXT PRIMARY KEY,  -- int/string selon le schéma
    sexe         TEXT,
    age          INT
);

CREATE TABLE IF NOT EXISTS gold.dim_geographie (
    id_geo       INT PRIMARY KEY,
    code_region  TEXT,
    libelle_region TEXT,
    pays         TEXT
);

CREATE TABLE IF NOT EXISTS gold.dim_etablissement (
    finess       TEXT PRIMARY KEY,
    nom          TEXT,
    id_geo       INT REFERENCES gold.dim_geographie(id_geo)
);

-- ============================================================
-- DIMENSIONS SPÉCIFIQUES (liées à une seule table de faits)
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.dim_diagnostic (
    code_diag    TEXT PRIMARY KEY,
    libelle      TEXT
);

-- only to Cons (uniquement liée à FAIT_CONSULTATION)
CREATE TABLE IF NOT EXISTS gold.dim_professionnel (
    id_professionnel TEXT PRIMARY KEY,
    nom              TEXT
);

-- ============================================================
-- TABLES DE FAITS
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.fait_hospitalisation (
    id_fait_hospitalisation BIGSERIAL PRIMARY KEY,
    id_temps     INT  NOT NULL REFERENCES gold.dim_temps(id_temps),
    id_patient   TEXT NOT NULL REFERENCES gold.dim_patient(id_patient),
    finess       TEXT NOT NULL REFERENCES gold.dim_etablissement(finess),
    code_diag    TEXT          REFERENCES gold.dim_diagnostic(code_diag),
    -- Mesures
    nb_hospitalisations INT NOT NULL DEFAULT 1,
    loaded_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gold.fait_consultation (
    id_fait_consultation BIGSERIAL PRIMARY KEY,
    id_temps         INT  NOT NULL REFERENCES gold.dim_temps(id_temps),
    id_patient       TEXT NOT NULL REFERENCES gold.dim_patient(id_patient),
    finess           TEXT NOT NULL REFERENCES gold.dim_etablissement(finess),
    id_professionnel TEXT          REFERENCES gold.dim_professionnel(id_professionnel),
    code_diag        TEXT          REFERENCES gold.dim_diagnostic(code_diag),
    -- Mesures
    duree_consultation INT,
    nb_consultations   INT NOT NULL DEFAULT 1,
    loaded_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gold.fait_deces (
    id_fait_deces BIGSERIAL PRIMARY KEY,
    id_temps  INT  NOT NULL REFERENCES gold.dim_temps(id_temps),
    id_geo    INT  NOT NULL REFERENCES gold.dim_geographie(id_geo),
    id_patient TEXT NOT NULL REFERENCES gold.dim_patient(id_patient),
    -- Mesures
    nb_deces  INT NOT NULL DEFAULT 1,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gold.fait_satisfaction (
    id_fait_satisfaction BIGSERIAL PRIMARY KEY,
    id_temps INT  NOT NULL REFERENCES gold.dim_temps(id_temps),
    finess   TEXT NOT NULL REFERENCES gold.dim_etablissement(finess),
    id_geo   INT  NOT NULL REFERENCES gold.dim_geographie(id_geo),
    -- Mesures
    score_global FLOAT,
    loaded_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fait_hospitalisation_date  ON gold.fait_hospitalisation(id_temps);
CREATE INDEX IF NOT EXISTS idx_fait_hospitalisation_etab  ON gold.fait_hospitalisation(finess);
CREATE INDEX IF NOT EXISTS idx_fait_consultation_date     ON gold.fait_consultation(id_temps);
CREATE INDEX IF NOT EXISTS idx_fait_consultation_etab     ON gold.fait_consultation(finess);
CREATE INDEX IF NOT EXISTS idx_fait_deces_date            ON gold.fait_deces(id_temps);
CREATE INDEX IF NOT EXISTS idx_fait_satisfaction_date     ON gold.fait_satisfaction(id_temps);
CREATE INDEX IF NOT EXISTS idx_fait_satisfaction_etab     ON gold.fait_satisfaction(finess);
