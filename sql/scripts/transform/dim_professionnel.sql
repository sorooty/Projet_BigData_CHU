-- Transformation et alimentation de la dimension propre
INSERT INTO gold.dim_professionnel (id_professionnel, nom)
SELECT 
    TRIM(id_prof_source),
    UPPER(TRIM(nom_source))
FROM gold.stg_professionnels_raw

-- S'il y a un doublon ou une mise à jour sur l'ID, on rafraîchit le nom
ON CONFLICT (id_professionnel) DO UPDATE 
SET nom = EXCLUDED.nom;