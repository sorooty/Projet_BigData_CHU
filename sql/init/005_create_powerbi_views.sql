-- Vues Gold pour connexion PowerBI.
-- Import mode recommande: requetes aggregees, rafraichissement quotidien apres pipeline.
-- DirectQuery possible sur ces vues mais deconseille en prod (volume).

-- KPI consultations: nb et duree par etablissement, region, periode, diagnostic, profil patient
CREATE OR REPLACE VIEW gold.v_kpi_consultations AS
SELECT
    e.finess,
    e.nom                       AS etablissement,
    g.code_region,
    g.libelle_region,
    t.annee,
    t.date_complete,
    d.code_diag,
    d.libelle                   AS diagnostic,
    p.sexe,
    p.age,
    SUM(f.nb_consultations)     AS nb_consultations,
    AVG(f.duree_consultation)   AS duree_moy_min
FROM gold.fait_consultation f
JOIN  gold.dim_temps        t ON t.id_temps  = f.id_temps
JOIN  gold.dim_patient      p ON p.id_patient = f.id_patient
JOIN  gold.dim_etablissement e ON e.finess   = f.finess
LEFT JOIN gold.dim_geographie  g ON g.id_geo  = e.id_geo
LEFT JOIN gold.dim_diagnostic  d ON d.code_diag = f.code_diag
GROUP BY
    e.finess, e.nom, g.code_region, g.libelle_region,
    t.annee, t.date_complete, d.code_diag, d.libelle,
    p.sexe, p.age;

-- KPI deces: nb par region et periode
CREATE OR REPLACE VIEW gold.v_kpi_deces AS
SELECT
    g.code_region,
    g.libelle_region,
    t.annee,
    t.date_complete,
    SUM(f.nb_deces) AS nb_deces
FROM gold.fait_deces f
JOIN gold.dim_temps       t ON t.id_temps = f.id_temps
JOIN gold.dim_geographie  g ON g.id_geo   = f.id_geo
GROUP BY g.code_region, g.libelle_region, t.annee, t.date_complete;

-- KPI satisfaction: score moyen par etablissement, region, periode
CREATE OR REPLACE VIEW gold.v_kpi_satisfaction AS
SELECT
    e.finess,
    e.nom               AS etablissement,
    g.code_region,
    g.libelle_region,
    t.annee,
    t.date_complete,
    AVG(f.score_global) AS score_moyen,
    COUNT(*)            AS nb_mesures
FROM gold.fait_satisfaction f
JOIN  gold.dim_temps        t ON t.id_temps = f.id_temps
JOIN  gold.dim_etablissement e ON e.finess  = f.finess
LEFT JOIN gold.dim_geographie g ON g.id_geo = f.id_geo
GROUP BY e.finess, e.nom, g.code_region, g.libelle_region, t.annee, t.date_complete;

-- KPI hospitalisations: agregation par etablissement, diagnostic, periode (vide jusqu ETL fait_hospitalisation)
CREATE OR REPLACE VIEW gold.v_kpi_hospitalisations AS
SELECT
    e.finess,
    e.nom               AS etablissement,
    g.libelle_region,
    t.annee,
    t.date_complete,
    d.code_diag,
    d.libelle           AS diagnostic,
    SUM(f.nb_hospitalisations) AS nb_hospitalisations
FROM gold.fait_hospitalisation f
JOIN  gold.dim_temps        t ON t.id_temps  = f.id_temps
JOIN  gold.dim_etablissement e ON e.finess   = f.finess
LEFT JOIN gold.dim_geographie  g ON g.id_geo = e.id_geo
LEFT JOIN gold.dim_diagnostic  d ON d.code_diag = f.code_diag
GROUP BY e.finess, e.nom, g.libelle_region, t.annee, t.date_complete, d.code_diag, d.libelle;
