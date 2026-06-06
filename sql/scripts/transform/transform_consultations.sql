-- Transformations HiveQL pour les tables Gold
-- Utilise les fichiers Bronze extraits par extract_postgres.py et extract_csv.py

-- ============================================================
-- TABLES BRONZE (CSV externes)
-- Ces tables pointent vers les fichiers CSV extraits dans /data/bronze
-- S'assurer que les fichiers dates_raw.csv, diagnostic_raw.csv,
-- patient_raw.csv et hospitalisations_raw.csv sont présents dans /data/bronze
-- ============================================================

CREATE EXTERNAL TABLE IF NOT EXISTS bronze.date_raw (
        date1 STRING,
        date2 STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = '"'
)
STORED AS TEXTFILE
LOCATION '/data/bronze/date_raw.csv'
TBLPROPERTIES ("skip.header.line.count"="1");

CREATE EXTERNAL TABLE IF NOT EXISTS bronze.diagnostic_raw (
        Code_diag STRING,
        Diagnostic STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = '"'
)
STORED AS TEXTFILE
LOCATION '/data/bronze/diagnostic_raw.csv'
TBLPROPERTIES ("skip.header.line.count"="1");

CREATE EXTERNAL TABLE IF NOT EXISTS bronze.patient_raw (
        Id_Patient INT,
        Nom STRING,
        Prenom STRING,
        Sexe STRING,
        Adresse STRING,
        Ville STRING,
        Code_postal STRING,
        Pays STRING,
        EMail STRING,
        Tel STRING,
        Date STRING,
        Age INT,
        Num_Secu STRING,
        Groupe_sanguin STRING,
        Poid STRING,
        Taille STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = '"'
)
STORED AS TEXTFILE
LOCATION '/data/bronze/patient_raw.csv'
TBLPROPERTIES ("skip.header.line.count"="1");

CREATE EXTERNAL TABLE IF NOT EXISTS bronze.hospitalisations_raw (
        Num_Hospitalisation STRING,
        Id_patient INT,
        identifiant_organisation STRING,
        Code_diagnostic STRING,
        Suite_diagnostic_consultation STRING,
        Date_Entree STRING,
        Jour_Hospitalisation STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar" = '"'
)
STORED AS TEXTFILE
LOCATION '/data/bronze/hospitalisations_raw.csv'
TBLPROPERTIES ("skip.header.line.count"="1");


-- PHASE TRANSFORMATION : Création des tables Gold à partir des données brutes

-- ============================================================
-- DIMENSION TEMPS
-- ============================================================
CREATE TABLE IF NOT EXISTS gold.dim_temps (
    id_temps INT,
    date_complete DATE,
    annee INT
)
STORED AS PARQUET;

INSERT OVERWRITE TABLE gold.dim_temps
SELECT
    row_number() OVER (ORDER BY dt) AS id_temps,
    dt AS date_complete,
    year(dt) AS annee
FROM (
    SELECT DISTINCT
        to_date(trim(date1), 'dd-MM-yyyy') AS dt
    FROM bronze.date_raw
    WHERE date1 IS NOT NULL
      AND trim(date1) != ''
) t
WHERE dt IS NOT NULL;

-- ============================================================
-- DIMENSION DIAGNOSTIC
-- ============================================================
CREATE TABLE IF NOT EXISTS gold.dim_diagnostic (
    code_diag STRING,
    libelle STRING
)
STORED AS PARQUET;

INSERT OVERWRITE TABLE gold.dim_diagnostic
SELECT
    Code_diag AS code_diag,
    Diagnostic AS libelle
FROM bronze.diagnostic_raw
WHERE Code_diag IS NOT NULL
  AND trim(Code_diag) != '';

-- ============================================================
-- DIMENSION PATIENT
-- ============================================================
CREATE TABLE IF NOT EXISTS gold.dim_patient (
    id_patient INT,
    sexe STRING,
    age INT
)
STORED AS PARQUET;

INSERT OVERWRITE TABLE gold.dim_patient
SELECT
    cast(Id_Patient AS INT) AS id_patient,
    CASE
        WHEN lower(trim(Sexe)) LIKE 'm%' THEN 'M'
        WHEN lower(trim(Sexe)) LIKE 'f%' THEN 'F'
        ELSE NULL
    END AS sexe,
    CASE
        WHEN trim(Age) = '' THEN NULL
        ELSE cast(Age AS INT)
    END AS age
FROM bronze.patient_raw
WHERE Id_Patient IS NOT NULL
  AND trim(Id_Patient) != '';

-- ============================================================
-- TABLE DE FAIT HOSPITALISATION
-- ============================================================
CREATE TABLE IF NOT EXISTS gold.fait_hospitalisation (
    id_fait_hospitalisation INT,
    id_temps INT,
    id_patient INT,
    code_diag STRING,
    nb_hospitalisation INT
)
STORED AS PARQUET;

INSERT OVERWRITE TABLE gold.fait_hospitalisation
SELECT
    row_number() OVER (
        ORDER BY h.Id_patient, h.Code_diagnostic
    ) AS id_fait_hospitalisation,
    t.id_temps AS id_temps,
    cast(h.Id_patient AS INT) AS id_patient,
    h.Code_diagnostic AS code_diag,
    CASE
        WHEN h.Jour_Hospitalisation IS NULL
          OR trim(h.Jour_Hospitalisation) = '' THEN NULL
        ELSE cast(h.Jour_Hospitalisation AS INT)
    END AS nb_hospitalisation
FROM bronze.hospitalisations_raw h
LEFT JOIN gold.dim_temps t
    ON t.date_complete = to_date(trim(h.Date_Entree), 'dd-MM-yyyy');
