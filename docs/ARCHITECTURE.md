---
title: ARCHITECTURE - Vue Technique
tags:
  - documentation
  - architecture
---

# Architecture Technique CHU

## Vue d'ensemble actuelle

Sources (PostgreSQL, CSV locaux)  
Extraction Python (Airflow)  
Bronze CSV (`/opt/airflow/data/bronze`)  
Load staging PostgreSQL (`gold.stg_*`)  
Transform SQL PostgreSQL  
Gold PostgreSQL (`gold.dim_*`, `gold.fait_*`)  
Metabase

## Orchestration Airflow

- DAG principal: `airflow/dags/chu_daily_pipeline.py`
- Schedule: quotidien à minuit
- Mode standard: consultations (extract, load, transform, validate)
- Mode étendu: activé avec `ENABLE_EXTENDED_FACTS=true` pour géographie, décès, satisfaction, établissements, professionnels

## Schéma Gold retenu

Le modèle de constellation retenu conserve les clés métier texte en production:

- `gold.dim_patient.id_patient` (TEXT)
- `gold.dim_etablissement.finess` (TEXT)
- `gold.dim_professionnel.id_professionnel` (TEXT)
- `gold.dim_diagnostic.code_diag` (TEXT)

Les dimensions de temps et géographie gardent leurs identifiants numériques:

- `gold.dim_temps.id_temps` (INT)
- `gold.dim_geographie.id_geo` (INT)

Les faits:

- `gold.fait_consultation`
- `gold.fait_hospitalisation`
- `gold.fait_deces`
- `gold.fait_satisfaction`

Les FKs des faits utilisent les clés ci-dessus, en cohérence avec `sql/init/003_create_gold_core.sql`.

## Zones de données

### Bronze
- Emplacement: `/opt/airflow/data/bronze`
- Format: CSV
- Produit par les scripts extract Python

### Staging PostgreSQL
- Schéma: `gold`
- Tables: `stg_consultations_raw`, `stg_geographie_raw`, `stg_deces_raw`, `stg_satisfaction_raw`, `stg_etablissements_raw`, `stg_professionnels_raw`

### Gold PostgreSQL
- Schéma: `gold`
- Tables dimensionnelles et de faits pour reporting

## Stratégie HiveQL

HiveQL n'est pas utilisé dans le pipeline principal actuel.

Positionnement retenu:

1. PostgreSQL Gold reste la source de vérité pour la BI standard.
2. HiveQL sera introduit comme couche analytique complémentaire si la volumétrie ou les besoins l'exigent.
3. L'alimentation Hive se fera via export depuis Gold PostgreSQL ou pipeline dédié, sans casser le flux Airflow principal.

## Strategie Metabase

Connexion recommandee:

1. Connecteur PostgreSQL sur la base `chu_data`
2. Consommation de vues metier dans le schema `gold` (`v_kpi_consultations`, `v_kpi_deces`, `v_kpi_satisfaction`, `v_kpi_hospitalisations`)
3. Rafraichissement des questions apres execution du DAG

Bonnes pratiques:

- Stabiliser le contrat des vues SQL avant publication
- Planifier le refresh apres la fin du DAG
- Limiter l'exposition aux tables techniques `stg_*`
- Garder PowerBI en backup uniquement

## Docker et services

Services actifs nécessaires:

- `postgres`
- `airflow-init`
- `airflow-webserver`
- `airflow-scheduler`

Le fichier `docker-compose.yml` est aligné sur cette architecture PostgreSQL.
