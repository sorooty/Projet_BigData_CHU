import pandas as pd
import psycopg2
import os
from pathlib import Path

def extract_professionnels():
    try:
        output_file = Path('/opt/airflow/data/bronze/professionnels_raw.csv')
        
        # Connexion à la source opérationnelle PostgreSQL (gérée par le docker-compose)
        conn = psycopg2.connect(
            host='postgres',
            database='chu',
            user=os.getenv('POSTGRES_USER', 'admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'admin')
        )
        
        # On extrait l'identifiant du professionnel (RPS / ADELI) et son nom
        query = "SELECT id_professionnel, nom_professionnel FROM source_personnel;"
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Nettoyage Bronze : Pas de PK nulle
        df = df.dropna(subset=['id_professionnel'])
        
        # Sauvegarde
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"Succès: {len(df)} professionnels extraits vers Bronze.")
        
    except Exception as e:
        print(f"Erreur extraction professionnels : {e}")
        raise

if __name__ == '__main__':
    extract_professionnels()