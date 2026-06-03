-- Base dédiée à Airflow, séparée de chu_data pour éviter que
-- un "docker-compose down -v" n'efface l'historique des runs.
-- Ce script s'exécute avant les autres (tri alphabétique).
CREATE DATABASE airflow;
