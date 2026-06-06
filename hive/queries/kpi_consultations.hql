-- KPI: Taux de consultation par etablissement, region, diagnostic, periode et profil patient.
-- Utilite analytique: segmentation multi-dimensionnelle sur gros volumes (MapReduce).

USE chu_analytics;

SELECT
    e.finess,
    e.nom                           AS etablissement,
    g.libelle_region,
    t.annee,
    d.code_diag,
    d.libelle                       AS diagnostic,
    p.sexe,
    SUM(f.nb_consultations)         AS nb_consultations,
    AVG(f.duree_consultation)       AS duree_moy_min,
    COUNT(DISTINCT f.id_patient)    AS nb_patients_distincts
FROM fait_consultation f
JOIN dim_temps        t ON t.id_temps    = f.id_temps
JOIN dim_patient      p ON p.id_patient  = f.id_patient
JOIN dim_etablissement e ON e.finess     = f.finess
LEFT JOIN dim_geographie  g ON g.id_geo  = e.id_geo
LEFT JOIN dim_diagnostic  d ON d.code_diag = f.code_diag
GROUP BY
    e.finess, e.nom, g.libelle_region,
    t.annee, d.code_diag, d.libelle, p.sexe
ORDER BY nb_consultations DESC;
