# CHU Data Platform

<p align="center">
  <a href="#demarrage-rapide"><img alt="Démarrage" src="https://img.shields.io/badge/D%C3%A9marrage-Rapide-0ea5e9?style=for-the-badge"></a>
  <a href="#architecture-cible"><img alt="Architecture" src="https://img.shields.io/badge/Architecture-Bronze%20Silver%20Gold-14b8a6?style=for-the-badge"></a>
  <a href="#roadmap-socle"><img alt="Roadmap" src="https://img.shields.io/badge/Roadmap-Socle-6366f1?style=for-the-badge"></a>
  <a href="#contribution-equipe"><img alt="Équipe" src="https://img.shields.io/badge/%C3%89quipe-4%20Membres-f59e0b?style=for-the-badge"></a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white">
  <img alt="Project status" src="https://img.shields.io/badge/Status-En%20initialisation-22c55e?style=flat-square">
</p>

Plateforme décisionnelle Big Data pour le contexte CHU.  
Objectif: intégrer des sources hétérogènes santé, alimenter un entrepôt analytique, et produire des KPI fiables pour le pilotage.

## Table des matières

- [Objectifs](#objectifs)
- [Architecture cible](#architecture-cible)
- [Structure du dépôt](#structure-du-dépôt)
- [Démarrage rapide](#demarrage-rapide)
- [Qualité et conformité](#qualité-et-conformité)
- [Roadmap socle](#roadmap-socle)
- [Contribution équipe](#contribution-equipe)

## Objectifs

- Centraliser les données de soins, établissements, satisfaction et décès.
- Industrialiser des pipelines ETL reproductibles.
- Alimenter un modèle décisionnel validé (constellation).
- Respecter strictement les contraintes RGPD sur les données de santé.

## Architecture cible

Pattern 3 zones:

- Bronze: ingestion brute et traçable des sources.
- Silver: nettoyage, normalisation, règles qualité, pseudonymisation.
- Gold: tables analytiques prêtes pour BI et KPI.

Stack visée: Docker, PostgreSQL, Python (ETL), notebook pour validation, couche de restitution en phase suivante.

## Structure du dépôt

La structure suivante est la cible du socle:

```text
.
├─ data/
│  ├─ bronze/
│  ├─ silver/
│  └─ gold/
├─ notebooks/
├─ sql/
│  ├─ init/
│  └─ marts/
├─ src/
│  ├─ etl/
│  ├─ core/
│  └─ quality/
├─ .env.example
├─ docker-compose.yml
└─ README.md
```

## Démarrage rapide

```powershell
Copy-Item .env.example .env
docker compose up -d
pip install -r requirements.txt
python -m src.etl.cli --job pilot_soins
```

Pré-requis:

1. Docker Desktop installé et démarré.
2. Python 3.11+ disponible en local.
3. Données source soins chargées dans `operational.consultations`.

## Qualité et conformité

- Contrôles qualité à chaque étape ETL (nulls, doublons, cohérence métier).
- Journalisation des exécutions de jobs.
- Pseudonymisation obligatoire avant chargement Gold.
- Interdiction des données nominatives dans les couches analytiques.

## Roadmap socle

- [x] Mettre en place `docker-compose` et la base PostgreSQL.
- [x] Créer les schémas techniques et analytiques.
- [x] Ajouter le module ETL commun (config, logs, qualité, RGPD).
- [ ] Livrer un pipeline pilote complet source soins.
- [ ] Ajouter notebook de validation et graphes de contrôle.

## Contribution équipe

Projet réalisé en équipe de 4.

- A: Infrastructure, base de données, scripts SQL.
- B: Socle Python ETL et outillage commun.
- C: Pipeline pilote source soins.
- D: Qualité, conformité RGPD, validation notebook.

## Références projet

