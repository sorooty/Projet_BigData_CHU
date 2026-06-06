-- TRANSFORM: DIM GEOGRAPHIE
-- Load geographie from bronze to gold

TRUNCATE TABLE gold.dim_geographie CASCADE;

INSERT INTO gold.dim_geographie (id_geo, code_region, libelle_region, pays)
SELECT 
    ROW_NUMBER() OVER (ORDER BY code_region) as id_geo,
    code_region,
    libelle_region,
    pays
FROM (
    SELECT DISTINCT
        code_region,
        libelle_region,
        pays
    FROM bronze.geographie_raw
    WHERE code_region IS NOT NULL
    ORDER BY code_region
) t;

SELECT COUNT(*) as "Rows Loaded" FROM gold.dim_geographie;
