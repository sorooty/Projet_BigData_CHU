-- Alimente gold.dim_professionnel depuis le staging.
-- DISTINCT ON élimine les doublons de id_prof_source avant l'upsert
-- (ON CONFLICT DO UPDATE échoue si la même clé apparaît deux fois).

WITH deduped AS (
    SELECT DISTINCT ON (TRIM(id_prof_source))
        TRIM(id_prof_source)       AS id_professionnel,
        NULLIF(TRIM(nom_source), '') AS nom
    FROM gold.stg_professionnels_raw
    WHERE NULLIF(TRIM(id_prof_source), '') IS NOT NULL
    ORDER BY TRIM(id_prof_source)
)
INSERT INTO gold.dim_professionnel (id_professionnel, nom)
SELECT id_professionnel, nom FROM deduped
ON CONFLICT (id_professionnel) DO UPDATE
SET
    nom = COALESCE(EXCLUDED.nom, gold.dim_professionnel.nom);
