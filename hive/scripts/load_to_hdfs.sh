#!/usr/bin/env bash
# Chargement des exports Gold CSV vers HDFS.
# A executer apres export_gold_to_csv.py.
#
# Usage: bash load_to_hdfs.sh [export_dir] [hdfs_root]

set -euo pipefail

EXPORT_DIR="${1:-/tmp/gold_export}"
HDFS_ROOT="${2:-/chu/data}"

echo "[HDFS] Creation des repertoires cibles..."
for table in dim_temps dim_patient dim_geographie dim_etablissement \
             dim_diagnostic dim_professionnel \
             fait_consultation fait_deces fait_satisfaction; do
    hdfs dfs -mkdir -p "${HDFS_ROOT}/gold/${table}"
done

echo "[HDFS] Depot des CSV..."
for csv_file in "${EXPORT_DIR}"/gold/*.csv; do
    table_name=$(basename "${csv_file}" .csv)
    hdfs dfs -put -f "${csv_file}" "${HDFS_ROOT}/gold/${table_name}/"
    echo "  OK: ${table_name}"
done

echo "[HIVE] Reparation des partitions fait_consultation..."
hive -e "USE chu_analytics; MSCK REPAIR TABLE fait_consultation;"

echo "[HDFS] Chargement termine."
