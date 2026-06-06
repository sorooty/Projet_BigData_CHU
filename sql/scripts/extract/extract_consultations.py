import pandas as pd
import psycopg2
import os
from pathlib import Path

def extract_consultations():
    try:
        output_file = Path('/opt/airflow/data/bronze/consultations_raw.csv')
        
        conn = psycopg2.connect(
            host='postgres',
            database='chu',
            user=os.getenv('POSTGRES_USER', 'admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'admin')
        )
        
        # On extrait les données de la table opérationnelle
        # Seyni pourra filtrer ici par date si on passe en mode incrémental quotidien
        query = """
            SELECT 
                id_patient, 
                date_consultation, 
                diagnostic as code_diag, 
                id_etablissement as finess, 
                id_professionnel,
                duree_consultation
            FROM consultation;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Sauvegarde brute (Bronze)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"Succès: {len(df)} lignes de consultation extraites vers Bronze.")
        
    except Exception as e:
        print(f"Erreur extraction consultations : {e}")
        raise

if __name__ == '__main__':
    extract_consultations()