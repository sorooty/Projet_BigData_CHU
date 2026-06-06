-- Nettoyage préalable si Seyni réexécute le job pour la même journée (Idempotence)
-- En production, on peut aussi filtrer ou faire un DELETE basé sur le lot du jour.
TRUNCATE TABLE gold.fait_consultation;

-- Insertion finale dans la table de faits
INSERT INTO gold.fait_consultation (
    id_temps,
    id_patient,
    id_etablissement,
    id_professionnel,
    code_diag,
    duree_consultation,
    nb_consultations
)
SELECT 
    -- 1. Transformation de la date en ID Temps (ex: 2026-06-05 -> 20260605)
    TO_CHAR(stg.date_consultation_src::date, 'YYYYMMDD')::INT as id_temps,
    
    -- 2. Récupération des clés étrangères depuis nos dimensions propres
    p.id_patient,
    e.id_etablissement,
    prof.id_professionnel,
    COALESCE(d.code_diag, 'UNKNOWN') as code_diag,
    
    -- 3. Injection des mesures physiques
    COALESCE(stg.duree_consult_src, 0) as duree_consultation,
    1 as nb_consultations -- Chaque ligne du staging équivaut à 1 acte de consultation
    
FROM gold.stg_consultations_raw stg
-- Jointures cruciales avec tes dimensions pour récupérer les clés techniques (Surrogate Keys)
INNER JOIN gold.dim_patient p ON stg.id_patient_src = p.patient_code
INNER JOIN gold.dim_etablissement e ON stg.finess_src = e.finess
INNER JOIN gold.dim_professionnel prof ON stg.id_prof_src = prof.id_professionnel
LEFT JOIN gold.dim_diagnostic d ON TRIM(stg.code_diag_src) = d.code_diag;