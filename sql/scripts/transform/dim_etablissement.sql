-- Insertion dans la dimension cible : DIM_ETABLISSEMENT
INSERT INTO gold.dim_etablissement (finess, nom, id_geo)
SELECT 
    stg.finess,
    stg.nom,
    geo.id_geo
FROM gold.stg_etablissements_raw stg
-- On joint avec la dimension géographie pour récupérer le bon id_geo (FK)
LEFT JOIN gold.dim_geographie geo ON stg.code_region = geo.code_region

-- Upsert : si le finess existe déjà, on met à jour les informations
ON CONFLICT (finess) DO UPDATE 
SET nom = EXCLUDED.nom,
    id_geo = EXCLUDED.id_geo;