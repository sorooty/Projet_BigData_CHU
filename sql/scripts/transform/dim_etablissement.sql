-- Alimente gold.dim_etablissement depuis le staging.

INSERT INTO gold.dim_etablissement (finess, nom, id_geo)
SELECT
    TRIM(stg.finess) AS finess,
    NULLIF(TRIM(stg.nom), '') AS nom,
    geo.id_geo
FROM gold.stg_etablissements_raw stg
LEFT JOIN gold.dim_geographie geo
    ON TRIM(stg.code_region) = geo.code_region
WHERE NULLIF(TRIM(stg.finess), '') IS NOT NULL
ON CONFLICT (finess) DO UPDATE
SET
    nom = COALESCE(EXCLUDED.nom, gold.dim_etablissement.nom),
    id_geo = COALESCE(EXCLUDED.id_geo, gold.dim_etablissement.id_geo);
