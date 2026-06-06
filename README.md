# CHU Data Pipeline

Plateforme Big Data décisionnelle pour le contexte CHU.

Objectif: orchestrer les pipelines ETL (Airflow), ingerer des sources heterogenes (PostgreSQL, CSV, FTP), transformer les donnees, et alimenter des rapports PowerBI.

## Structure du projet

```
chu-pipeline/
├── airflow/
│   ├── dags/                     # DAGs Airflow (orchestration)
│   │   ├── chu_daily_pipeline.py # Main DAG
│   │   └── utils.py              # Helpers (run_python_script, run_sql_on_postgres, etc)
│   └── ...
├── sql/
│   ├── scripts/                  # Scripts exécutés par DAGs
│   │   ├── extract/              # Extract Python (PostgreSQL, CSV)
│   │   ├── transform/            # Transform SQL PostgreSQL
│   │   ├── load/                 # Load Python (staging PostgreSQL)
│   │   └── validate_gold.py      # Data quality
│   └── init/                     # Schema DDL (init DB)
├── docker/                       # Dockerfiles + docker-compose.yml
├── powerbi/                      # Models + rapports PowerBI
├── data/
│   ├── raw/                      # Fichiers sources CSV locaux (non versionnes)
│   ├── bronze/                   # Extractions brutes produites par les scripts
│   ├── silver/                   # Donnees nettoyees, normalisees
│   └── gold/                     # Donnees analytiques
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

## Donnees sources et dossier raw

- Les CSV sources a traiter doivent etre places dans `data/raw/` (local).
- Dans le conteneur Airflow, ce dossier est monte en `/opt/airflow/data/raw`.
- Le script `sql/scripts/extract/extract_csv.py` lit uniquement les fichiers `*.csv` presents directement dans ce dossier.
- Les fichiers de `data/raw/` sont ignores par Git. Seul `data/raw/.gitkeep` est versionne pour conserver le dossier.
- Le dump PostgreSQL source reste dans `project_data/BDD PostgreSQL/DATA2023` et sert a alimenter la base source `postgres`.

### Perspectives

- `sql/scripts/extract/extract_ftp.py` reste en reserve si une source FTP apparait plus tard.
- Pour le moment, le pipeline utilise seulement PostgreSQL et les CSV locaux de `data/raw/`.
- Les traitements geographie, deces et satisfaction sont disponibles et activables via `ENABLE_EXTENDED_FACTS=true`.

## Architecture

| Zone | Type | Contenu | Outil |
|------|------|---------|-------|
| **Bronze** | Files | CSV extraits, bruts | CSV in `/opt/airflow/data/bronze/` |
| **Silver** | Files | Données nettoyées, normalisées | Zone optionnelle |
| **Gold** | Tables | Tables analytiques | PostgreSQL (schema `gold`) |

### Modele de constellation retenu

- Le modele cible conserve les cles metier texte existantes:
  - `dim_etablissement.finess` comme cle reference etablissement
  - `dim_patient.id_patient` en texte
  - `dim_professionnel.id_professionnel` en texte
- Les tables de faits referencent ces cles metier, pas des surrogate keys entieres pour ces dimensions.

### HiveQL et analytique

- Le pipeline principal Airflow execute PostgreSQL uniquement.
- HiveQL est positionne comme couche analytique complementaire pour gros volumes ou usages exploratoires.
- Si active ensuite, il sera alimente depuis Gold PostgreSQL ou via export dedie.

### Connexion PowerBI

1. Source principale: PostgreSQL schema `gold`
2. Utiliser des vues metier stables pour les rapports
3. Mode recommande: Import pour commencer, puis DirectQuery sur vues ciblees si necessaire
4. Rafraichissement apres execution DAG quotidienne

**Orchestration:** Apache Airflow (daily @ 00:00 UTC)

**Restitution:** PowerBI connecté à PostgreSQL (Gold)

## Documentation
- (*WIP*)

## Roadmap

- [x] Phase 1: Restructuration dirs + stubs
- [x] Phase 2: Docker (compose, Dockerfile, env)
- [ ] Phase 3: DAGs complets + utils
- [ ] Phase 4: Collègues écrivent scripts
- [ ] Phase 5: PowerBI + validation
