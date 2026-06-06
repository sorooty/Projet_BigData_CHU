-- Tables externes Hive pointant vers des exports CSV du Gold PostgreSQL.
-- Utilisation: analyses volumineuses sur cluster Hadoop (MapReduce / Spark sur Hive).
-- Les CSV sont a deposer dans HDFS avant execution: hdfs dfs -put gold_export/ /chu/data/

-- Base de travail CHU
CREATE DATABASE IF NOT EXISTS chu_analytics
COMMENT 'Entrepot analytique CHU - couche Gold';

USE chu_analytics;

-- Dimension temps
CREATE EXTERNAL TABLE IF NOT EXISTS dim_temps (
    id_temps        INT,
    date_complete   STRING,
    annee           INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/chu/data/gold/dim_temps/'
TBLPROPERTIES ('skip.header.line.count'='1');

-- Dimension patient
CREATE EXTERNAL TABLE IF NOT EXISTS dim_patient (
    id_patient  STRING,
    sexe        STRING,
    age         INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/chu/data/gold/dim_patient/'
TBLPROPERTIES ('skip.header.line.count'='1');

-- Dimension geographie
CREATE EXTERNAL TABLE IF NOT EXISTS dim_geographie (
    id_geo          INT,
    code_region     STRING,
    libelle_region  STRING,
    pays            STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/chu/data/gold/dim_geographie/'
TBLPROPERTIES ('skip.header.line.count'='1');

-- Dimension etablissement
CREATE EXTERNAL TABLE IF NOT EXISTS dim_etablissement (
    finess  STRING,
    nom     STRING,
    id_geo  INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/chu/data/gold/dim_etablissement/'
TBLPROPERTIES ('skip.header.line.count'='1');

-- Dimension diagnostic
CREATE EXTERNAL TABLE IF NOT EXISTS dim_diagnostic (
    code_diag   STRING,
    libelle     STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/chu/data/gold/dim_diagnostic/'
TBLPROPERTIES ('skip.header.line.count'='1');

-- Fait consultation (partitionnee par annee pour les scans)
CREATE EXTERNAL TABLE IF NOT EXISTS fait_consultation (
    id_fait_consultation    BIGINT,
    id_temps                INT,
    id_patient              STRING,
    finess                  STRING,
    id_professionnel        STRING,
    code_diag               STRING,
    duree_consultation      INT,
    nb_consultations        INT
)
PARTITIONED BY (annee INT)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS ORC
LOCATION '/chu/data/gold/fait_consultation/'
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- Fait deces
CREATE EXTERNAL TABLE IF NOT EXISTS fait_deces (
    id_fait_deces   BIGINT,
    id_temps        INT,
    id_geo          INT,
    id_patient      STRING,
    nb_deces        INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS ORC
LOCATION '/chu/data/gold/fait_deces/'
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- Fait satisfaction
CREATE EXTERNAL TABLE IF NOT EXISTS fait_satisfaction (
    id_fait_satisfaction    BIGINT,
    id_temps                INT,
    finess                  STRING,
    id_geo                  INT,
    score_global            DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS ORC
LOCATION '/chu/data/gold/fait_satisfaction/'
TBLPROPERTIES ('orc.compress'='SNAPPY');
