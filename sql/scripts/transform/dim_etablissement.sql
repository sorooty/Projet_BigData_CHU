-- NOTE POUR SEYNI : Dans le script de création de la table (003_create_gold_core.sql), 
-- la table gold.dim_etablissement doit impérativement avoir :
-- 1. id_etablissement SERIAL PRIMARY KEY (pour s'auto-incrémenter)
-- 2. finess VARCHAR UNIQUE (indispensable pour le ON CONFLICT ci-dessous)

INSERT INTO gold.dim_etablissement (finess, nom, id_geo)
SELECT 
    TRIM(stg.finess),
    UPPER(TRIM(stg.nom)), -- Standardisation en majuscules pour nettoyer le texte
    geo.id_geo
FROM gold.stg_etablissements_raw stg
LEFT JOIN gold.dim_geographie geo ON TRIM(stg.code_region) = geo.code_region

-- L'upsert se base sur la clé métier finess (qui doit être contrainte UNIQUE en base)
ON CONFLICT (finess) DO UPDATE 
SET nom = EXCLUDED.nom,
    id_geo = EXCLUDED.id_geo;