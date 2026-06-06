-- KPI: Deces par region et periode.
-- Utilite analytique: detection de surmortalite regionale et tendances annuelles.

USE chu_analytics;

SELECT
    g.code_region,
    g.libelle_region,
    t.annee,
    SUM(f.nb_deces)                 AS nb_deces,
    COUNT(DISTINCT f.id_patient)    AS nb_patients_decedes
FROM fait_deces f
JOIN dim_temps      t ON t.id_temps = f.id_temps
JOIN dim_geographie g ON g.id_geo   = f.id_geo
GROUP BY g.code_region, g.libelle_region, t.annee
ORDER BY t.annee DESC, nb_deces DESC;
