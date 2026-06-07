-- Alimente gold.dim_etablissement depuis le staging.
-- Les FINESS sont normalises pour eviter les ecarts de format (zeros a gauche).

WITH source_rows AS (
    SELECT DISTINCT
        COALESCE(NULLIF(REGEXP_REPLACE(TRIM(stg.finess), '^0+', ''), ''), '0') AS finess_norm,
        NULLIF(TRIM(stg.nom), '') AS nom,
        geo.id_geo
    FROM gold.stg_etablissements_raw stg
    LEFT JOIN gold.dim_geographie geo
        ON TRIM(stg.code_region) = geo.code_region
    WHERE NULLIF(TRIM(stg.finess), '') IS NOT NULL
)
UPDATE gold.dim_etablissement e
SET
    nom = COALESCE(s.nom, e.nom),
    id_geo = COALESCE(s.id_geo, e.id_geo)
FROM source_rows s
WHERE COALESCE(NULLIF(REGEXP_REPLACE(TRIM(e.finess), '^0+', ''), ''), '0') = s.finess_norm;

WITH source_rows AS (
    SELECT DISTINCT
        COALESCE(NULLIF(REGEXP_REPLACE(TRIM(stg.finess), '^0+', ''), ''), '0') AS finess_norm,
        NULLIF(TRIM(stg.nom), '') AS nom,
        geo.id_geo
    FROM gold.stg_etablissements_raw stg
    LEFT JOIN gold.dim_geographie geo
        ON TRIM(stg.code_region) = geo.code_region
    WHERE NULLIF(TRIM(stg.finess), '') IS NOT NULL
)
INSERT INTO gold.dim_etablissement (finess, nom, id_geo)
SELECT
    s.finess_norm,
    s.nom,
    s.id_geo
FROM source_rows s
WHERE NOT EXISTS (
    SELECT 1
    FROM gold.dim_etablissement e
    WHERE COALESCE(NULLIF(REGEXP_REPLACE(TRIM(e.finess), '^0+', ''), ''), '0') = s.finess_norm
);
