-- Transformation consultations pour le modele gold PostgreSQL.
-- La table de staging gold.stg_consultations_raw est chargee avant ce script.

TRUNCATE TABLE
    gold.fait_consultation,
    gold.dim_temps,
    gold.dim_patient,
    gold.dim_etablissement,
    gold.dim_diagnostic
RESTART IDENTITY CASCADE;

INSERT INTO gold.dim_temps (id_temps, date_complete, annee)
SELECT DISTINCT
    TO_CHAR(s.date_consultation::date, 'YYYYMMDD')::INT AS id_temps,
    s.date_consultation::date AS date_complete,
    EXTRACT(YEAR FROM s.date_consultation::date)::INT AS annee
FROM gold.stg_consultations_raw s
ORDER BY 1;

INSERT INTO gold.dim_patient (id_patient, sexe, age)
SELECT DISTINCT
    s.id_patient::TEXT,
    NULL,
    NULL
FROM gold.stg_consultations_raw s
ORDER BY 1;

INSERT INTO gold.dim_etablissement (finess, nom, id_geo)
SELECT DISTINCT
    s.id_etablissement::TEXT,
    NULL,
    NULL
FROM gold.stg_consultations_raw s
ORDER BY 1;

INSERT INTO gold.dim_diagnostic (code_diag, libelle)
SELECT DISTINCT
    COALESCE(NULLIF(TRIM(s.diagnostic), ''), 'UNKNOWN') AS code_diag,
    NULL
FROM gold.stg_consultations_raw s
ORDER BY 1;

INSERT INTO gold.fait_consultation (
    id_temps,
    id_patient,
    finess,
    id_professionnel,
    code_diag,
    duree_consultation,
    nb_consultations
)
SELECT
    TO_CHAR(s.date_consultation::date, 'YYYYMMDD')::INT AS id_temps,
    s.id_patient::TEXT AS id_patient,
    s.id_etablissement::TEXT AS finess,
    NULL AS id_professionnel,
    COALESCE(NULLIF(TRIM(s.diagnostic), ''), 'UNKNOWN') AS code_diag,
    NULL AS duree_consultation,
    1 AS nb_consultations
FROM gold.stg_consultations_raw s
ORDER BY 1, 2, 3;
