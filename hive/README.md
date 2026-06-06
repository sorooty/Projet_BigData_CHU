# Couche HiveQL analytique - CHU

## Rôle dans l'architecture

Le pipeline principal (Airflow + PostgreSQL Gold) couvre l'ETL quotidien et les vues PowerBI.

HiveQL intervient comme **couche analytique complémentaire** sur Hadoop/HDFS pour :
- les requêtes MapReduce sur gros volumes (années de données)
- les analyses de tendances multi-régions sans impacter PostgreSQL
- les traitements batch ponctuels (rapports annuels, études épidémiologiques)

## Flux de données

```
PostgreSQL Gold --> export CSV --> HDFS /chu/data/gold/ --> Hive tables externes --> requêtes HiveQL
```

## Structure

```
hive/
  ddl/
    create_external_tables.hql   -- tables externes Hive (pointent vers HDFS)
  queries/
    kpi_consultations.hql        -- taux consultation par etablissement/diagnostic/profil
    kpi_deces.hql                -- surmortalite par region et periode
    kpi_satisfaction.hql         -- classement satisfaction etablissements
```

## Format de stockage

- Tables de faits : ORC + compression Snappy (lectures analytiques rapides)
- `fait_consultation` : partitionnée par `annee` pour limiter les scans

## Utilisation

1. Exporter les tables Gold depuis PostgreSQL vers CSV
2. Déposer dans HDFS : `hdfs dfs -put gold_export/ /chu/data/gold/`
3. Lancer les DDL : `hive -f hive/ddl/create_external_tables.hql`
4. Exécuter les requêtes : `hive -f hive/queries/kpi_consultations.hql`
