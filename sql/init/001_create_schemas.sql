-- Schémas de base du projet.
-- operational: source brute applicative
-- bronze/silver/gold: pipeline décisionnel
-- audit: logs techniques des runs ETL
CREATE SCHEMA IF NOT EXISTS operational;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS audit;
