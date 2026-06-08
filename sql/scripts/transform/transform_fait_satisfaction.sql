-- Alimente gold.fait_satisfaction depuis le staging.

INSERT INTO gold.dim_temps (id_temps, date_complete, annee, trimestre, mois, semaine)
SELECT DISTINCT
    TO_CHAR(s.date_mesure_src::date, 'YYYYMMDD')::INT AS id_temps,
    s.date_mesure_src::date AS date_complete,
    EXTRACT(YEAR    FROM s.date_mesure_src::date)::INT AS annee,
    EXTRACT(QUARTER FROM s.date_mesure_src::date)::INT AS trimestre,
    EXTRACT(MONTH   FROM s.date_mesure_src::date)::INT AS mois,
    EXTRACT(WEEK    FROM s.date_mesure_src::date)::INT AS semaine
FROM gold.stg_satisfaction_raw s
ON CONFLICT (id_temps) DO UPDATE
SET
    date_complete = EXCLUDED.date_complete,
    annee         = EXCLUDED.annee,
    trimestre     = EXCLUDED.trimestre,
    mois          = EXCLUDED.mois,
    semaine       = EXCLUDED.semaine;

INSERT INTO gold.dim_etablissement (finess, nom, id_geo)
SELECT DISTINCT
    TRIM(s.finess_src) AS finess,
    NULL::TEXT AS nom,
    g.id_geo
FROM gold.stg_satisfaction_raw s
INNER JOIN gold.dim_geographie g
    ON g.code_region = TRIM(s.code_region_src)
WHERE NULLIF(TRIM(s.finess_src), '') IS NOT NULL
ON CONFLICT (finess) DO UPDATE
SET id_geo = COALESCE(EXCLUDED.id_geo, gold.dim_etablissement.id_geo);

TRUNCATE TABLE gold.fait_satisfaction RESTART IDENTITY;

INSERT INTO gold.fait_satisfaction (
    id_temps,
    finess,
    id_geo,
    score_global
)
SELECT
    TO_CHAR(s.date_mesure_src::date, 'YYYYMMDD')::INT AS id_temps,
    TRIM(s.finess_src) AS finess,
    g.id_geo,
    s.score_global_src::FLOAT AS score_global
FROM gold.stg_satisfaction_raw s
INNER JOIN gold.dim_geographie g
    ON g.code_region = TRIM(s.code_region_src)
WHERE NULLIF(TRIM(s.finess_src), '') IS NOT NULL;
