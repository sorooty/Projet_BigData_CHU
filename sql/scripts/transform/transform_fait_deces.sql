-- TRANSFORM: FAIT DECES
-- Load deces from bronze to gold

TRUNCATE TABLE gold.fait_deces CASCADE;

INSERT INTO gold.fait_deces (id_temps, id_geo, id_patient, nb_deces)
SELECT 
    1 as id_temps,
    COALESCE(dg.id_geo, 1) as id_geo,
    'PATIENT_' || dr.id as id_patient,
    1 as nb_deces
FROM bronze.deces_raw dr
LEFT JOIN gold.dim_geographie dg ON SUBSTRING(dr.code_lieu_deces, 1, 2) = dg.code_region
WHERE dr.sexe IS NOT NULL;

SELECT COUNT(*) as "Rows Loaded" FROM gold.fait_deces;
