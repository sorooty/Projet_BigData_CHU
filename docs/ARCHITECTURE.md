---
title: ARCHITECTURE - Vue Technique
tags:
  - documentation
  - architecture
---

# Architecture Technique CHU

## Vue d'ensemble

```
Sources (PostgreSQL, CSV, FTP)
    ↓
EXTRACT (Python scripts)
    ↓
Bronze Zone (/data/bronze/*.csv)
    ↓
TRANSFORM (HiveQL scripts)
    ↓
Silver/Gold Zone (Hive tables, Parquet)
    ↓
PowerBI (Dashboards)
```

---

## Orchestration: Apache Airflow

**DAG Principal**: `airflow/dags/chu_daily_pipeline.py`

**Schedule**: Quotidien à minuit (0 0 * * *)

**Phases**:
1. **Extract** (Parallèle)
   - `extract_postgres.py` → /data/bronze/consultations_raw.csv
   - `extract_csv.py` → /data/bronze/*.csv

2. **Transform** (Séquentiel)
   - Exécute HiveQL scripts
   - Crée dimensions + faits
   - Format Parquet

3. **Load**
   - Charge dans Hive Gold

4. **Validate**
   - Checks qualité

5. **Notify**
   - Slack/email si succès/erreur

---

## Zones de Données

### Bronze (Brutes)
- **Emplacement**: `/data/bronze/`
- **Format**: CSV
- **Source**: Extract Python scripts
- **Rétention**: 7 jours (archivage après)
- **Traçabilité**: Toutes colonnes sources

### Silver (Nettoyées)
- **Emplacement**: `/data/silver/` (ou Hive si volumes)
- **Format**: Parquet
- **Transformations**: Validation, normalisation, pseudonymisation RGPD
- **Rétention**: 30 jours
- **Qualité**: Data quality checks passés

### Gold (Analytiques)
- **Emplacement**: Hive/Hadoop tables
- **Format**: Parquet (columnar, compressé)
- **Structure**: Modèle dimensionnel (faits + dimensions)
- **Partitionné**: Par year_month
- **Optimisé**: Pour PowerBI (requêtes rapides)
- **Consommateurs**: PowerBI, rapports

---

## Modèle Dimensionnel

### Tables de Dimension
- `dim_patient`: patient_code, sexe, age_groupe, region
- `dim_etablissement`: code, nom, region, type
- `dim_diagnostic`: code, libellé, catégorie, type
- `dim_date`: date, day_of_week, month, quarter, year
- `dim_deces`: code, cause, region, age_groupe

### Tables de Fait
- `fait_consultation`: nb_consultations, montant_total, duration
  - Keys: id_patient, id_etablissement, id_diagnostic, date_id
  - Partitionné par year_month

- `fait_hospitalisation`: nb_hospitalisations, duration, cost
  - Keys: id_patient, id_etablissement, id_diagnostic, date_id
  - Partitionné par year_month

---

## Stockage & Performance

### Hive/Hadoop
- **NameNode**: Service master HDFS
- **DataNode**: Réplication données
- **HiveServer**: Requêtes SQL-like

### Optimisations
- **Format**: Parquet (compression 80%, read 10x faster)
- **Partitioning**: /year_month (skip partitions inutiles)
- **Bucketing**: Pour joins fréquents (si applicable)
- **Indexes**: Crés automatiquement sur clés
- **Stats**: ANALYZE TABLE pour optimiseur requêtes

### Exemples Performance
- CSV 10GB → Parquet 2GB
- Requête "consultations par region" : 30s → 3s

---

## Infrastructure Docker

### Services
| Service | Image | Port | Rôle |
|---------|-------|------|------|
| postgres | postgres:16-alpine | 5432 | Source données (Bronze/Silver) |
| airflow-webserver | airflow:custom | 8080 | Interface DAGs |
| airflow-scheduler | airflow:custom | - | Exécute DAGs quotidiens |
| airflow-redis | redis:7 | 6379 | Queue backend Airflow |
| hive-metastore | apachehive:custom | 9083 | Métadonnées Hive |
| hive-server | apachehive:custom | 10000 | Requêtes HiveQL |
| hadoop-namenode | bde2020/hadoop-namenode | 9870 | HDFS NameNode |
| hadoop-datanode | bde2020/hadoop-datanode | 50075 | HDFS DataNode |

### Volumes
- `postgres_data:/var/lib/postgresql/data` → Persistance BD
- `/data/bronze/` → Bronze zone
- `/data/silver/` → Silver zone
- `/airflow/dags/` → DAGs
- `/scripts/` → Extract/transform/load scripts

---

## PowerBI Connection

**Connexion Hive**:
- **Host**: `hive-server`
- **Port**: `10000`
- **Database**: `default`
- **Tables**: `gold.fait_*`, `gold.dim_*`
- **Mode**: Direct query (optimal pour Hive/big data)

**Refresh Schedule**:
- Après DAG complète (~6h du matin)
- Frequence: Quotidienne

**Data Model**:
- Importez dimensions dans PowerBI
- Faits en DirectQuery (volumétrie)
- Relations sur clés ID

---

## Sécurité & RGPD

### Pseudonymisation
- Bronze: données nominatives brutes
- Silver: pseudonymisation appliquée
- Gold: pas de données nominatives, juste ID

### Audit
- Tous les scripts loggent executions
- Airflow logs centralisés
- Audit trail pour conformité

### Accès
- PostgreSQL: user/pass (env vars)
- Hive: aucun auth (network isolated)
- Airflow: authentification locale

---

## Monitoring & Observabilité

### Logs
- **Airflow logs**: Centralisés dans interface Airflow
- **Script logs**: Loggés dans les scripts (logging.py)
- **Hive logs**: HDFS logs

### Alertes
- DAG failure → Slack notification
- Task retry → Log warning
- Data quality fail → Alert

### Dashboards
- Airflow UI: DAG status, task history
- (Optionnel) Grafana: System metrics (CPU, memory, IO)

---

## Scalabilité

### Phase 1 (Actuel)
- Docker local
- PostgreSQL mono-nœud
- Hive mono-nœud (HDFS local)
- Airflow local

### Phase 2 (Futur)
- Docker → Kubernetes
- PostgreSQL → RDS managed
- Hadoop → Cloud HDFS (EMR/Dataproc)
- Airflow → Managed Airflow (Composer/MWAA)

---

## Nommage & Conventions

### Scripts
- **Extract**: `extract_<source>.py` (ex: `extract_postgres.py`)
- **Transform**: `<action>_<entity>.sql` (ex: `transform_consultations.sql`)
- **Load**: `load_<target>.py` (ex: `load_to_warehouse.py`)

### Tables Hive
- **Schema**: `gold` (production analytique)
- **Dimension**: `dim_<entity>` (ex: `dim_patient`)
- **Fact**: `fait_<event>` (ex: `fait_consultation`)
- **Partition**: `year_month` (ex: `2025-01`)

### Variables/Configs
- Env vars: `UPPERCASE_SNAKE_CASE` (ex: `POSTGRES_HOST`)
- Code vars: `snake_case` (ex: `pg_host`)
- Constants: `CONSTANT_CASE`

---

## Troubleshooting

### DAG ne s'exécute pas
1. Vérifier interface Airflow: http://localhost:8080
2. Vérifier logs Airflow: `docker-compose logs airflow-scheduler`
3. Vérifier syntaxe DAG: `airflow dags validate`

### Script échoue
1. Tester localement: `docker-compose exec ... python script.py`
2. Vérifier logs script
3. Vérifier connectivité (PostgreSQL, Hive)

### Hive requête slow
1. Vérifier partitions utilisées: `EXPLAIN QUERY`
2. Vérifier indexes: `SHOW INDEXES`
3. Considérer bucketing
4. Augmenter executor memory (docker-compose)

---

## Références Importantes

- Plan d'implémentation: `Plan_Implémentation_CHU_Final.md`
- Modèle métier: `Referentiel_de_données_Groupe2_Seyni.pdf` (pages 9-12)
- Workflow Git: `WORKFLOW.md`
- Rôles: `ROLES.md`
