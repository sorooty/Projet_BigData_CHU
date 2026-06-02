-- Dimensions minimales pour démarrer les analyses.
CREATE TABLE IF NOT EXISTS gold.dim_temps (
    date_key DATE PRIMARY KEY,
    annee INT NOT NULL,
    trimestre INT NOT NULL,
    mois INT NOT NULL,
    semaine INT NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.dim_etablissement (
    etablissement_id TEXT PRIMARY KEY,
    nom_etablissement TEXT,
    region TEXT
);

-- Table de faits pilote pour valider le flux soins de bout en bout.
CREATE TABLE IF NOT EXISTS gold.fait_consultation (
    consultation_id BIGSERIAL PRIMARY KEY,
    consultation_source_id TEXT UNIQUE NOT NULL,
    date_key DATE NOT NULL REFERENCES gold.dim_temps(date_key),
    etablissement_id TEXT REFERENCES gold.dim_etablissement(etablissement_id),
    diagnostic_code TEXT,
    professionnel_id TEXT,
    patient_hash TEXT NOT NULL,
    nb_consultations INT NOT NULL DEFAULT 1,
    duree_minutes INT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index de base pour les filtres les plus courants.
CREATE INDEX IF NOT EXISTS idx_fait_consultation_date ON gold.fait_consultation(date_key);
CREATE INDEX IF NOT EXISTS idx_fait_consultation_etab ON gold.fait_consultation(etablissement_id);
