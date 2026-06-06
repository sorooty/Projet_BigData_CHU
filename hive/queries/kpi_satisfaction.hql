-- KPI: Satisfaction par etablissement et region.
-- Utilite analytique: classement des etablissements, ecarts regionaux, evolution annuelle.

USE chu_analytics;

SELECT
    e.finess,
    e.nom               AS etablissement,
    g.code_region,
    g.libelle_region,
    t.annee,
    AVG(f.score_global) AS score_moyen,
    MIN(f.score_global) AS score_min,
    MAX(f.score_global) AS score_max,
    COUNT(*)            AS nb_mesures
FROM fait_satisfaction f
JOIN  dim_temps         t ON t.id_temps = f.id_temps
JOIN  dim_etablissement e ON e.finess   = f.finess
LEFT JOIN dim_geographie g ON g.id_geo  = f.id_geo
GROUP BY e.finess, e.nom, g.code_region, g.libelle_region, t.annee
ORDER BY t.annee DESC, score_moyen DESC;
