-- TRANSFORM: FAIT SATISFACTION
TRUNCATE TABLE gold.fait_satisfaction CASCADE;

INSERT INTO gold.fait_satisfaction (id_temps, finess, id_geo, score_global)
SELECT 
    1 as id_temps,
    sr.finess,
    1 as id_geo,
    sr.score as score_global
FROM bronze.satisfaction_raw sr
WHERE sr.finess IS NOT NULL 
  AND sr.score IS NOT NULL;

SELECT COUNT(*) as "Rows Loaded" FROM gold.fait_satisfaction;
