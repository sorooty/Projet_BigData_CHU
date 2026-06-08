-- =============================================================================
-- VUES METABASE — 8 KPI CHU (Cloud Healthcare Unit)
-- =============================================================================
-- Besoins utilisateurs (source : sujet de projet CESI BLOC 6 Big Data) :
--   1. Taux de consultation par établissement et par période
--   2. Taux de consultation par diagnostic et par période
--   3. Taux global d'hospitalisation par période
--   4. Taux d'hospitalisation par diagnostic et par période
--   5. Taux d'hospitalisation par sexe et par âge
--   6. Taux de consultation par professionnel
--   7. Nombre de décès par région — année 2019
--   8. Taux global de satisfaction par région — année 2020
--
-- Usage Metabase : New > Native Query > PostgreSQL chu_data > SELECT * FROM gold.v_kpi_xxx
-- Ou directement via "Browse data" > gold > vues v_kpi_*
-- =============================================================================


-- -----------------------------------------------------------------------------
-- KPI 1 : Consultations par établissement et par année
-- Graphique recommandé : Barre groupée (finess/libellé sur X, année en couleur)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold.v_kpi_consultation_etablissement AS
-- Note : id_etablissement des consultations (ex: 10004431671) est un ID
-- interne qui ne correspond pas aux codes FINESS officiels (9 chiffres).
-- Le nom officiel n'est pas disponible → on affiche le code comme label.
SELECT
    f.finess,
    COALESCE(e.nom, 'Étab. ' || f.finess)    AS etablissement,
    COALESCE(g.libelle_region, 'Région inconnue') AS region,
    t.annee,
    t.trimestre,
    SUM(f.nb_consultations)                   AS nb_consultations
FROM gold.fait_consultation f
JOIN gold.dim_temps t
    ON t.id_temps = f.id_temps
LEFT JOIN gold.dim_etablissement e
    ON e.finess = f.finess AND e.nom IS NOT NULL
LEFT JOIN gold.dim_geographie g
    ON g.id_geo = e.id_geo
GROUP BY f.finess, e.nom, g.libelle_region, t.annee, t.trimestre
ORDER BY t.annee DESC, nb_consultations DESC;


-- -----------------------------------------------------------------------------
-- KPI 2 : Consultations par diagnostic et par année
-- Graphique recommandé : Ligne (un diagnostic = une couleur, année sur X)
-- Filtre Metabase : WHERE annee = {{annee}} pour filtrage interactif
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold.v_kpi_consultation_diagnostic AS
SELECT
    f.code_diag,
    COALESCE(d.libelle, f.code_diag)          AS diagnostic,
    t.annee,
    t.trimestre,
    SUM(f.nb_consultations)                   AS nb_consultations
FROM gold.fait_consultation f
JOIN gold.dim_temps t
    ON t.id_temps = f.id_temps
LEFT JOIN gold.dim_diagnostic d
    ON d.code_diag = f.code_diag
WHERE f.code_diag IS NOT NULL
GROUP BY f.code_diag, d.libelle, t.annee, t.trimestre
ORDER BY t.annee DESC, nb_consultations DESC;


-- -----------------------------------------------------------------------------
-- KPI 3 : Hospitalisation globale par période
-- Graphique recommandé : Ligne (année sur X, total sur Y)
-- Note : fait_hospitalisation actuellement vide — la vue retourne 0 lignes
--        jusqu'au chargement des données.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold.v_kpi_hospitalisation_globale AS
SELECT
    t.annee,
    t.trimestre,
    SUM(f.nb_hospitalisations)                AS nb_hospitalisations
FROM gold.fait_hospitalisation f
JOIN gold.dim_temps t
    ON t.id_temps = f.id_temps
GROUP BY t.annee, t.trimestre
ORDER BY t.annee ASC, t.trimestre ASC;


-- -----------------------------------------------------------------------------
-- KPI 4 : Hospitalisation par diagnostic et par période
-- Graphique recommandé : Barre groupée (diagnostic sur X, année en couleur)
-- Note : fait_hospitalisation actuellement vide.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold.v_kpi_hospitalisation_diagnostic AS
SELECT
    f.code_diag,
    COALESCE(d.libelle, f.code_diag)          AS diagnostic,
    t.annee,
    t.trimestre,
    SUM(f.nb_hospitalisations)                AS nb_hospitalisations
FROM gold.fait_hospitalisation f
JOIN gold.dim_temps t
    ON t.id_temps = f.id_temps
LEFT JOIN gold.dim_diagnostic d
    ON d.code_diag = f.code_diag
WHERE f.code_diag IS NOT NULL
GROUP BY f.code_diag, d.libelle, t.annee, t.trimestre
ORDER BY t.annee DESC, nb_hospitalisations DESC;


-- -----------------------------------------------------------------------------
-- KPI 5 : Consultations par sexe et tranche d'âge
-- (Proxy hospitalisation car fait_hospitalisation est vide)
-- Graphique recommandé : Barre groupée ou Tableau croisé (sexe × tranche)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold.v_kpi_demographie AS
SELECT
    COALESCE(p.sexe, 'Non renseigné')         AS sexe,
    CASE
        WHEN p.age IS NULL    THEN 'Non renseigné'
        WHEN p.age < 18       THEN '< 18 ans'
        WHEN p.age < 30       THEN '18 – 29 ans'
        WHEN p.age < 50       THEN '30 – 49 ans'
        WHEN p.age < 70       THEN '50 – 69 ans'
        ELSE                       '70 ans et +'
    END                                       AS tranche_age,
    t.annee,
    SUM(f.nb_consultations)                   AS nb_consultations,
    ROUND(AVG(p.age::numeric), 1)             AS age_moyen
FROM gold.fait_consultation f
JOIN gold.dim_patient p
    ON p.id_patient = f.id_patient
JOIN gold.dim_temps t
    ON t.id_temps = f.id_temps
GROUP BY sexe, tranche_age, t.annee
ORDER BY t.annee DESC, nb_consultations DESC;


-- -----------------------------------------------------------------------------
-- KPI 6 : Consultations par professionnel
-- Graphique recommandé : Scalar (total) + Barre horizontale si données liées
-- Note : id_professionnel n'est pas renseigné dans fait_consultation pour
--        les données actuelles. La vue expose les professionnels connus
--        et leurs consultations liées (0 pour l'instant).
--        Utiliser v_kpi_professionnels_total pour le KPI scalaire.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold.v_kpi_consultation_professionnel AS
SELECT
    pr.id_professionnel,
    COALESCE(pr.nom, 'Inconnu')               AS nom_professionnel,
    t.annee,
    COALESCE(SUM(f.nb_consultations), 0)      AS nb_consultations
FROM gold.dim_professionnel pr
LEFT JOIN gold.fait_consultation f
    ON f.id_professionnel = pr.id_professionnel
LEFT JOIN gold.dim_temps t
    ON t.id_temps = f.id_temps
GROUP BY pr.id_professionnel, pr.nom, t.annee
ORDER BY nb_consultations DESC;

-- Scalaire : nombre total de professionnels enregistrés dans le système
CREATE OR REPLACE VIEW gold.v_kpi_professionnels_total AS
SELECT
    COUNT(*)                                  AS nb_professionnels_enregistres,
    COUNT(DISTINCT f.id_professionnel)        AS nb_professionnels_actifs
FROM gold.dim_professionnel pr
LEFT JOIN gold.fait_consultation f
    ON f.id_professionnel = pr.id_professionnel;


-- -----------------------------------------------------------------------------
-- KPI 7 : Décès par région — filtre par défaut 2019
-- Graphique recommandé : Barre horizontale (région sur Y, total sur X)
-- Note : fait_deces en cours de chargement. Retourne 0 lignes si pas encore
--        chargé. Supprimer le filtre WHERE pour voir toutes les années.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold.v_kpi_deces_region AS
SELECT
    g.code_region,
    COALESCE(g.libelle_region, g.code_region) AS region,
    t.annee,
    SUM(f.nb_deces)                           AS nb_deces
FROM gold.fait_deces f
JOIN gold.dim_temps t
    ON t.id_temps = f.id_temps
JOIN gold.dim_geographie g
    ON g.id_geo = f.id_geo
GROUP BY g.code_region, g.libelle_region, t.annee
ORDER BY t.annee DESC, nb_deces DESC;


-- -----------------------------------------------------------------------------
-- KPI 8 : Satisfaction globale par région — filtre par défaut 2020
-- Graphique recommandé : Jauge/Gauge (0–100) ou Barre horizontale
-- Note : fait_satisfaction disponible (8 984 lignes).
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold.v_kpi_satisfaction_region AS
SELECT
    g.code_region,
    COALESCE(g.libelle_region, g.code_region) AS region,
    t.annee,
    ROUND(AVG(f.score_global)::numeric, 1)    AS satisfaction_moyenne,
    COUNT(*)                                   AS nb_reponses
FROM gold.fait_satisfaction f
JOIN gold.dim_temps t
    ON t.id_temps = f.id_temps
JOIN gold.dim_geographie g
    ON g.id_geo = f.id_geo
GROUP BY g.code_region, g.libelle_region, t.annee
ORDER BY t.annee DESC, satisfaction_moyenne DESC;


-- =============================================================================
-- VÉRIFICATION RAPIDE (à coller dans psql après exécution)
-- =============================================================================
-- SELECT viewname FROM pg_views WHERE schemaname = 'gold' ORDER BY viewname;
--
-- SELECT * FROM gold.v_kpi_consultation_etablissement LIMIT 5;
-- SELECT * FROM gold.v_kpi_consultation_diagnostic    LIMIT 5;
-- SELECT * FROM gold.v_kpi_hospitalisation_globale    LIMIT 5;
-- SELECT * FROM gold.v_kpi_hospitalisation_diagnostic LIMIT 5;
-- SELECT * FROM gold.v_kpi_demographie                LIMIT 5;
-- SELECT * FROM gold.v_kpi_consultation_professionnel LIMIT 5;
-- SELECT * FROM gold.v_kpi_deces_region               LIMIT 5;
-- SELECT * FROM gold.v_kpi_satisfaction_region        LIMIT 5;
-- =============================================================================
