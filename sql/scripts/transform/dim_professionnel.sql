-- Alimente gold.dim_professionnel depuis le staging.

INSERT INTO gold.dim_professionnel (id_professionnel, nom)
SELECT
    TRIM(id_prof_source) AS id_professionnel,
    NULLIF(TRIM(nom_source), '') AS nom
FROM gold.stg_professionnels_raw
WHERE NULLIF(TRIM(id_prof_source), '') IS NOT NULL
ON CONFLICT (id_professionnel) DO UPDATE
SET
    nom = COALESCE(EXCLUDED.nom, gold.dim_professionnel.nom);
