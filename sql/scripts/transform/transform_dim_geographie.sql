-- Alimente gold.dim_geographie depuis le staging.

WITH source_rows AS (
    SELECT DISTINCT
        TRIM(code_region_src) AS code_region,
        NULLIF(TRIM(libelle_region_src), '') AS libelle_region,
        COALESCE(NULLIF(TRIM(pays_src), ''), 'FRANCE') AS pays
    FROM gold.stg_geographie_raw
    WHERE NULLIF(TRIM(code_region_src), '') IS NOT NULL
),
existing_rows AS (
    SELECT
        s.code_region,
        s.libelle_region,
        s.pays,
        g.id_geo AS existing_id_geo
    FROM source_rows s
    LEFT JOIN gold.dim_geographie g
        ON g.code_region = s.code_region
),
max_id AS (
    SELECT COALESCE(MAX(id_geo), 0) AS base_id
    FROM gold.dim_geographie
),
new_rows AS (
    SELECT
        m.base_id + ROW_NUMBER() OVER (ORDER BY e.code_region) AS id_geo,
        e.code_region,
        e.libelle_region,
        e.pays
    FROM existing_rows e
    CROSS JOIN max_id m
    WHERE e.existing_id_geo IS NULL
)
INSERT INTO gold.dim_geographie (id_geo, code_region, libelle_region, pays)
SELECT
    n.id_geo,
    n.code_region,
    n.libelle_region,
    n.pays
FROM new_rows n;

UPDATE gold.dim_geographie g
SET
    libelle_region = e.libelle_region,
    pays = e.pays
FROM existing_rows e
WHERE g.id_geo = e.existing_id_geo
  AND (
        COALESCE(g.libelle_region, '') <> COALESCE(e.libelle_region, '')
     OR COALESCE(g.pays, '') <> COALESCE(e.pays, '')
  );
