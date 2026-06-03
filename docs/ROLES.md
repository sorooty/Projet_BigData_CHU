---
title: ROLES - Responsabilités Équipe
tags:
  - documentation
  - roles
---

# Rôles & Responsabilités

## Chef de Projet / DevOps (Seyni)

### Infrastructure & Orchestration
- Crée & maintient `docker-compose.yml`
- Crée & maintient `Dockerfile` (Airflow, Hive, etc)
- Maintient `requirements.txt`
- Configure Airflow, PostgreSQL, Hive, Hadoop
- Gère les logs et le monitoring

### DAGs Airflow
- Crée `airflow/dags/chu_daily_pipeline.py`
- Définit l'ordre des tâches (dependencies)
- Ajoute/intègre les scripts des collègues comme tâches
- Gère error handling, retries, alertes

### Review & Merge
- Review toutes les PRs (logique, performance, tests)
- Teste les scripts localement avant merge
- Merge sur main
- Redéploie et vérifie

### À NE PAS FAIRE
❌ Écrire les scripts métier (extract/transform/load) — c'est collègues
❌ Laisser collègues modifier docker-compose ou DAGs

---

## Développeurs (Collègues)

### Responsabilité Commune
Tous les développeurs écrivent les **scripts métier**:

### Types de Scripts

#### 1. Extract (Python)
- Connexion sources (PostgreSQL, CSV, FTP)
- Extraction données brutes
- Validation basique
- Sauvegarde CSV dans `/data/bronze/`
- **Fichiers**: `sql/scripts/extract/*.py`

#### 2. Transform (HiveQL)
- Requêtes Hive complexes
- Création dimensions (dim_patient, dim_etablissement, etc)
- Création faits (fait_consultation, fait_hospitalisation, etc)
- Partitionnement, optimisations
- Format Parquet
- **Fichiers**: `sql/scripts/transform/*.sql`

#### 3. Load (Python)
- Exécution requêtes HiveQL
- Insertion/upsert dans Gold
- Vérification chargement
- **Fichiers**: `sql/scripts/load/*.py`

### Workflow Développeur
1. Créer branche `feature/mon-job`
2. Coder le script (extract/transform/load)
3. Tester localement
4. Commit + push
5. Créer PR
6. Attendre review Seyni

### À NE PAS FAIRE
❌ Modifier `docker-compose.yml`
❌ Modifier `Dockerfile`
❌ Modifier `airflow/dags/chu_daily_pipeline.py`
❌ Updater `requirements.txt` (demander à Seyni si librairie manquante)
❌ Merger PRs (Seyni le fait)

---

## Matrice Responsabilités

| Aspect | Seyni | Collègues |
|--------|-------|-----------|
| **Infrastructure** | ✅ Crée & maintient | ❌ NE TOUCHE PAS |
| **Docker** | ✅ Dockerfiles | ❌ Utilise juste |
| **DAGs Airflow** | ✅ Crée & intègre scripts | ❌ NE TOUCHE PAS |
| **Scripts Extract** | ❌ | ✅ Écrit |
| **Scripts Transform** | ❌ | ✅ Écrit |
| **Scripts Load** | ❌ | ✅ Écrit |
| **Review PR** | ✅ Review toutes | ❌ Review entre pairs ok |
| **Merge PR** | ✅ Merge | ❌ Pas merging |
| **Monitoring** | ✅ Logs, alertes | ❌ |
| **Debugging** | ✅ Infra bugs | ✅ Script bugs |

---

## Niveau d'Access Git (Recommandé)

### Seyni
- Accès admin au repo
- Peut merger sur main
- Peut push/force directement

### Collègues
- Accès contributeur
- Peuvent créer branches
- Peuvent push sur branches feature/*
- ❌ Pas d'accès main
- ❌ Pas de merge rights

---

## Communication

- **Slack**: Questions rapides, blockers
- **GitHub Issues**: Bugs, features à faire
- **PRs**: Discussions détaillées, review formal
- **Docs**: Updates après chaque changement majeur

---

## Escalade en cas de Blocage

1. Script échoue localement → Ask channel Slack
2. Pas de réponse 2h → Ping Seyni direct
3. Infra cassée → Seyni prioritaire (production impact)
