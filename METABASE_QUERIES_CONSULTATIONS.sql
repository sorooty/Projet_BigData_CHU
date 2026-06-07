/*
DASHBOARD CHU - VERSION CONSULTATIONS UNIQUEMENT
================================================

Seules les tables avec données sont utilisées :
- fait_consultation (1M+ lignes) ✓
- fact_hospitalisation (0 lignes) ✗
- fact_deces (0 lignes) ✗
- fact_satisfaction (0 lignes) ✗

Les 3 requêtes suivantes suffisent pour démarrer.
*/

-- Q1: TOP 10 Établissements - Consultation par année
-- TYPE GRAPHIQUE: Barre groupée
SELECT f.finess, t.annee, SUM(f.nb_consultations) AS total_consultations
FROM gold.fait_consultation f
JOIN gold.dim_temps t ON t.id_temps = f.id_temps
WHERE f.finess IN (
    SELECT finess FROM (
        SELECT finess, SUM(nb_consultations) as vol
        FROM gold.fait_consultation
        GROUP BY finess
        ORDER BY vol DESC
        LIMIT 10
    ) top_finess
)
GROUP BY f.finess, t.annee
ORDER BY t.annee DESC, total_consultations DESC;

---

-- Q2: TOP 15 Diagnostics - Consultation par année
-- TYPE GRAPHIQUE: Ligne
SELECT f.code_diag, d.libelle AS diagnostic, t.annee, SUM(f.nb_consultations) AS total_consultations
FROM gold.fait_consultation f
JOIN gold.dim_temps t ON t.id_temps = f.id_temps
LEFT JOIN gold.dim_diagnostic d ON d.code_diag = f.code_diag
WHERE f.code_diag IS NOT NULL
  AND f.code_diag IN (
      SELECT code_diag FROM (
          SELECT code_diag, SUM(nb_consultations) as vol
          FROM gold.fait_consultation
          GROUP BY code_diag
          ORDER BY vol DESC
          LIMIT 15
      ) top_diag
  )
GROUP BY f.code_diag, d.libelle, t.annee
ORDER BY t.annee ASC, total_consultations DESC;

---

-- Q6: KPI Consultations 2023
-- TYPE GRAPHIQUE: Nombres (3 chiffres clés séparés)
SELECT 
    'Total consultations 2023' AS metric,
    SUM(f.nb_consultations) AS value
FROM gold.fait_consultation f
JOIN gold.dim_temps t ON t.id_temps = f.id_temps
WHERE t.annee = 2023;

---

-- BONUS: Consultations par sexe/âge (TOP 10 tranches)
-- TYPE GRAPHIQUE: Tableau ou Barre
SELECT 
    p.sexe,
    CASE 
        WHEN p.age < 18 THEN '<18'
        WHEN p.age < 30 THEN '18-30'
        WHEN p.age < 50 THEN '30-50'
        WHEN p.age < 70 THEN '50-70'
        ELSE '70+'
    END AS age_tranche,
    SUM(f.nb_consultations) AS nb_consultations,
    AVG(p.age) AS age_moyen
FROM gold.fait_consultation f
JOIN gold.dim_patient p ON p.id_patient = f.id_patient
WHERE p.sexe IS NOT NULL AND p.age IS NOT NULL
GROUP BY p.sexe, age_tranche
ORDER BY nb_consultations DESC;

---

/*
INSTRUCTIONS METABASE:
1. Créer 4 nouvelles questions (New > Native Query)
2. Coller chaque SQL ci-dessus
3. Visualizer avec les types recommandés
4. Créer 1 Dashboard "CHU - Consultations 2023"
5. Ajouter les 4 questions au dashboard
6. Partager avec l'équipe

PROCHAINES ÉTAPES (quand données dispo):
- Q3: Hospitalisation globale (fait_hospitalisation)
- Q7: Décès régions 2019 (fait_deces)
- Q8: Satisfaction régions 2020 (fait_satisfaction)
*/
