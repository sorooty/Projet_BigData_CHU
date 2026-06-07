/*
GUIDE METABASE - CRÉER LES 8 QUESTIONS KPI CHU
==============================================

Chaque requête SQL ci-dessous doit être collée dans Metabase
New > Native Query > PostgreSQL chu_data > Copier/coller

Puis Visualize et choisir le type de graphique.

---
*/

-- Q1: TOP 10 Établissements - Consultation par année
-- TYPE GRAPHIQUE: Barre groupée (finess sur X, année en couleurs)
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

-- Q2: Consultation par diagnostic + période
-- TYPE GRAPHIQUE: Ligne (diagnostic unique en couleur, année sur X)
-- OU Barre groupée si tu veux top 10 diagnostics
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
ORDER BY t.annee DESC, total_consultations DESC;

---

-- Q3: Hospitalisation globale par période
-- TYPE GRAPHIQUE: Ligne (année sur X, total sur Y)
SELECT t.annee, SUM(f.nb_hospitalisations) AS total_hospitalisations
FROM gold.fait_hospitalisation f
JOIN gold.dim_temps t ON t.id_temps = f.id_temps
GROUP BY t.annee
ORDER BY t.annee ASC;

---

-- Q4: Hospitalisation par diagnostic + période
-- TYPE GRAPHIQUE: Barre groupée (diagnostic sur X, année en couleurs)
SELECT f.code_diag, d.libelle AS diagnostic, t.annee, SUM(f.nb_hospitalisations) AS total_hospitalisations
FROM gold.fait_hospitalisation f
JOIN gold.dim_temps t ON t.id_temps = f.id_temps
LEFT JOIN gold.dim_diagnostic d ON d.code_diag = f.code_diag
WHERE f.code_diag IS NOT NULL
  AND f.code_diag IN (
      SELECT code_diag FROM (
          SELECT code_diag, SUM(nb_hospitalisations) as vol
          FROM gold.fait_hospitalisation
          GROUP BY code_diag
          ORDER BY vol DESC
          LIMIT 15
      ) top_diag
  )
GROUP BY f.code_diag, d.libelle, t.annee
ORDER BY t.annee DESC, total_hospitalisations DESC;

---

-- Q5: Hospitalisation par sexe + âge
-- TYPE GRAPHIQUE: Pivot / Tableau croisé (sexe sur X, age sur Y, valeur = somme)
SELECT p.sexe, p.age, t.annee, SUM(f.nb_consultations) AS consultations
FROM gold.fait_consultation f
JOIN gold.dim_patient p ON p.id_patient = f.id_patient
JOIN gold.dim_temps t ON t.id_temps = f.id_temps
WHERE p.sexe IS NOT NULL AND p.age IS NOT NULL
GROUP BY p.sexe, p.age, t.annee
ORDER BY t.annee DESC, p.sexe, p.age;

---

-- Q6: KPI Consultations par professionnel
-- TYPE GRAPHIQUE: Nombres (3 chiffres clés)
-- Utiliser Metabase Scalar pour 3 questions séparées
SELECT 
    'Total consultations 2023' AS metric,
    SUM(f.nb_consultations) AS value
FROM gold.fait_consultation f
JOIN gold.dim_temps t ON t.id_temps = f.id_temps
WHERE t.annee = 2023;

-- OU pour le nombre de professionnels :
SELECT 
    'Nombre de professionnels actifs' AS metric,
    COUNT(DISTINCT f.id_professionnel) AS value
FROM gold.fait_consultation f
WHERE f.id_professionnel IS NOT NULL;

---

-- Q7: Décès par région 2019
-- TYPE GRAPHIQUE: Barre horizontale (région sur Y, total sur X)
SELECT g.libelle_region, SUM(f.nb_deces) AS total_deces
FROM gold.fait_deces f
JOIN gold.dim_temps t ON t.id_temps = f.id_temps
JOIN gold.dim_geographie g ON g.id_geo = f.id_geo
WHERE t.annee = 2019
GROUP BY g.libelle_region
ORDER BY total_deces DESC;

---

-- Q8: Satisfaction par région 2020
-- TYPE GRAPHIQUE: Jauge/Gauge (0-100) OU Barre horizontale
SELECT g.libelle_region, ROUND(AVG(f.score_global)::numeric, 1) AS satisfaction_moyenne
FROM gold.fait_satisfaction f
JOIN gold.dim_temps t ON t.id_temps = f.id_temps
JOIN gold.dim_geographie g ON g.id_geo = f.id_geo
WHERE t.annee = 2020
GROUP BY g.libelle_region
ORDER BY satisfaction_moyenne DESC;

---

/*
ÉTAPES POUR CRÉER LE DASHBOARD:
1. Créer chaque question une par une (Copier SQL > New Query > Coller > Visualize)
2. Une fois les 8 questions créées :
   - Click sur Menu > Dashboards > New Dashboard > "CHU KPI"
   - Ajouter les 8 questions au dashboard
   - Organiser en grille :
     - Haut : Q6 (3 KPI en nombres)
     - Milieu : Q2 (diag) + Q3 (hosp)
     - Bas : Q7 (décès) + Q8 (satisfaction)
     - Onglets : Q1 (étab), Q4 (hosp diag), Q5 (sexe/âge)
3. Partager le dashboard avec l'équipe
*/
