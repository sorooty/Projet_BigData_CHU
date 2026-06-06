-- Alimente gold.fait_deces depuis le staging.

INSERT INTO gold.dim_temps (id_temps, date_complete, annee)
SELECT DISTINCT
    TO_CHAR(s.date_deces_src::date, 'YYYYMMDD')::INT AS id_temps,
    s.date_deces_src::date AS date_complete,
    EXTRACT(YEAR FROM s.date_deces_src::date)::INT AS annee
FROM gold.stg_deces_raw s
ON CONFLICT (id_temps) DO UPDATE
SET
    date_complete = EXCLUDED.date_complete,
    annee = EXCLUDED.annee;

INSERT INTO gold.dim_patient (id_patient, sexe, age)
SELECT DISTINCT
    TRIM(s.id_patient_src) AS id_patient,
    NULL::TEXT AS sexe,
    NULL::INT AS age
FROM gold.stg_deces_raw s
WHERE NULLIF(TRIM(s.id_patient_src), '') IS NOT NULL
ON CONFLICT (id_patient) DO NOTHING;

TRUNCATE TABLE gold.fait_deces RESTART IDENTITY;

INSERT INTO gold.fait_deces (
    id_temps,
    id_geo,
    id_patient,
    nb_deces
)
SELECT
    TO_CHAR(s.date_deces_src::date, 'YYYYMMDD')::INT AS id_temps,
    g.id_geo,
    TRIM(s.id_patient_src) AS id_patient,
    COALESCE(s.nb_deces_src, 1) AS nb_deces
FROM gold.stg_deces_raw s
INNER JOIN gold.dim_geographie g
    ON g.code_region = TRIM(s.code_region_src)
WHERE NULLIF(TRIM(s.id_patient_src), '') IS NOT NULL;
