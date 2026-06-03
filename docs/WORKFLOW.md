---
title: WORKFLOW - Git & PR Process
tags:
  - documentation
  - workflow
---

# Workflow Git & PR Process

## Pour les Collègues (Développeurs)

### 1. Créer une branche
```bash
git checkout main
git pull origin main
git checkout -b feature/nom-feature
```

**Convention**: `feature/extract-postgres`, `feature/transform-consultations`, etc.

### 2. Coder
Créer/modifier les scripts dans `sql/scripts/`:
- `sql/scripts/extract/*.py` → extraction
- `sql/scripts/transform/*.sql` → transformations HiveQL
- `sql/scripts/load/*.py` → chargement

### 3. Tester localement
```bash
# Tester un script Python
docker-compose exec airflow python sql/scripts/extract/extract_postgres.py

# Tester une requête HiveQL
docker-compose exec hive-server hive -f sql/scripts/transform/transform_consultations.sql
```

### 4. Committer
```bash
git add sql/scripts/...
git commit -m "feat: extraction PostgreSQL consultations"
```

**Convention de messages**:
- `feat:` pour nouvelle feature
- `fix:` pour bug
- `refactor:` pour changement code sans impact
- Messages clairs en français

### 5. Pousser & Créer PR
```bash
git push origin feature/nom-feature
```

Créer une PR sur GitHub avec:
- Titre clair
- Description: quoi/pourquoi/comment tester
- Screenshots si applicable

### 6. Attendre Review
- Seyni review le code
- Répond aux remarques
- Seyni merge quand ok

---

## Pour Chef de Projet (Seyni)

### 1. Review PR
- Logique du code
- Performance (requêtes optimisées)
- Tests (couverts)
- Documentation

### 2. Tester localement
```bash
git fetch origin
git checkout origin/feature/nom-feature
# Tester le script
docker-compose exec ... python/hive ...
```

### 3. Intégrer dans DAG
Ajouter une tâche dans `airflow/dags/chu_daily_pipeline.py`:
```python
task_name = PythonOperator(
    task_id='task_name',
    python_callable=run_python_script,
    op_kwargs={'script': '/scripts/extract/extract_postgres.py'}
)
```

### 4. Merger
```bash
git checkout main
git merge origin/feature/nom-feature
git push origin main
```

### 5. Redéployer
```bash
docker-compose down
docker-compose up -d
# Vérifier DAG: http://localhost:8080
```

---

## Restrictions Strictes

❌ **Collègues ne doivent JAMAIS:**
- Toucher `docker-compose.yml`
- Modifier `Dockerfile`
- Changer `airflow/dags/chu_daily_pipeline.py`
- Updater `requirements.txt` (demander à Seyni)
- Merger leurs propres PRs

---

## Protections GitHub (À configurer)

1. Main branch protégée
   - Require PR reviews (minimum 1, Seyni)
   - Require status checks (linting, tests)
   - Dismiss stale PR approvals
   - Require branches up to date

2. Collègues restreints à PRs, pas d'accès merge
