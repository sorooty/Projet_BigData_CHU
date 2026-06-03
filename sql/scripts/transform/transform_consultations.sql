-- Stub: Création dimensions et faits
-- À compléter par les collègues avec vrai logique

-- Exemple structure pour dim_patient
CREATE TABLE IF NOT EXISTS gold.dim_patient (
    id_patient INT,
    patient_code STRING,
    sexe STRING,
    age_groupe STRING,
    region STRING
)
STORED AS PARQUET;

-- Exemple structure pour fait_consultation
CREATE TABLE IF NOT EXISTS gold.fait_consultation (
    id_patient INT,
    id_etablissement INT,
    id_diagnostic INT,
    date_id INT,
    nb_consultations INT,
    montant_total DECIMAL(10, 2)
)
PARTITIONED BY (year_month STRING)
STORED AS PARQUET;

-- À compléter: INSERT avec vrai transformations
