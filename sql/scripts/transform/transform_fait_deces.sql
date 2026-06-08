-- Alimente gold.fait_deces depuis le staging.

INSERT INTO gold.dim_temps (id_temps, date_complete, annee, trimestre, mois, semaine)
SELECT DISTINCT
    TO_CHAR(s.date_deces_src::date, 'YYYYMMDD')::INT AS id_temps,
    s.date_deces_src::date AS date_complete,
    EXTRACT(YEAR    FROM s.date_deces_src::date)::INT AS annee,
    EXTRACT(QUARTER FROM s.date_deces_src::date)::INT AS trimestre,
    EXTRACT(MONTH   FROM s.date_deces_src::date)::INT AS mois,
    EXTRACT(WEEK    FROM s.date_deces_src::date)::INT AS semaine
FROM gold.stg_deces_raw s
ON CONFLICT (id_temps) DO UPDATE
SET
    date_complete = EXCLUDED.date_complete,
    annee         = EXCLUDED.annee,
    trimestre     = EXCLUDED.trimestre,
    mois          = EXCLUDED.mois,
    semaine       = EXCLUDED.semaine;

TRUNCATE TABLE gold.fait_deces RESTART IDENTITY;

INSERT INTO gold.fait_deces (
    id_temps,
    id_geo,
    nb_deces
)
SELECT
    TO_CHAR(s.date_deces_src::date, 'YYYYMMDD')::INT AS id_temps,
    g.id_geo,
    SUM(COALESCE(s.nb_deces_src, 1)) AS nb_deces
FROM gold.stg_deces_raw s
INNER JOIN gold.dim_geographie g
    ON g.code_region = TRIM(s.code_region_src)
GROUP BY
    TO_CHAR(s.date_deces_src::date, 'YYYYMMDD')::INT,
    g.id_geo;
