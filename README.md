# CHU Data Pipeline

Plateforme Big Data décisionnelle pour le contexte CHU.

Objectif: orchestrer les pipelines ETL (Airflow), ingérer des sources hétérogènes (PostgreSQL, CSV, FTP), transformer avec Hive, et alimenter des rapports PowerBI.

## Structure du projet

```
chu-pipeline/
├── airflow/
│   ├── dags/                     # DAGs Airflow (orchestration)
│   │   ├── chu_daily_pipeline.py # Main DAG
│   │   └── utils.py              # Helpers (run_python_script, run_hive_query, etc)
│   └── ...
├── sql/
│   ├── scripts/                  # Scripts exécutés par DAGs
│   │   ├── extract/              # Extract Python (PostgreSQL, CSV)
│   │   ├── transform/            # Transform HiveQL
│   │   ├── load/                 # Load Python (Hive warehouse)
│   │   └── validate_gold.py      # Data quality
│   └── init/                     # Schema DDL (init DB)
├── docker/                       # Dockerfiles + docker-compose.yml
├── powerbi/                      # Models + rapports PowerBI
├── data/
│   ├── bronze/                   # Raw extracted files (CSV, Parquet)
│   ├── silver/                   # Cleaned, normalized files
│   └── gold/                     # Hive tables (analytics-ready)
├── docs/
│   ├── WORKFLOW.md              # Git + PR process
│   ├── ROLES.md                 # Rôles & responsabilités
│   └── ARCHITECTURE.md          # Tech stack & zones
└── README.md
```

## Démarrage rapide

1. **Setup local:**
   ```powershell
   cp .env.example .env
   docker-compose up -d
   ```

2. **Vérifier Airflow:**
   - URL: `http://localhost:8080`
   - Login: `airflow / airflow`

3. **Voir les DAGs:**
   - Airflow UI > DAGs
   - DAG `chu_daily_pipeline` doit être visible

## Architecture

| Zone | Type | Contenu | Outil |
|------|------|---------|-------|
| **Bronze** | Files | CSV extraits, bruts | Parquet in `/data/bronze/` |
| **Silver** | Files | Données nettoyées, normalisées | Parquet in `/data/silver/` |
| **Gold** | Tables | Tables Hive analytiques | Hive in Hadoop |

**Orchestration:** Apache Airflow (daily @ 00:00 UTC)

**Restitution:** PowerBI connecté à Hive (Gold)

## Documentation
- (*WIP*)

## Roadmap

- [x] Phase 1: Restructuration dirs + stubs
- [x] Phase 2: Docker (compose, Dockerfile, env)
- [ ] Phase 3: DAGs complets + utils
- [ ] Phase 4: Collègues écrivent scripts
- [ ] Phase 5: PowerBI + validation
