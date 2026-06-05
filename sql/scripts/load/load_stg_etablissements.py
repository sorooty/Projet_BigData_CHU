import psycopg2
import os

def load_staging_etablissements():
    # Seyni gère ces variables d'environnement dans le docker-compose
    conn = psycopg2.connect(
        host='postgres',
        database='chu',
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin')
    )
    cur = conn.cursor()
    
    try:
        # 1. Création de la table de staging (les colonnes reflètent le CSV source)
        # On suppose que le CSV contient un code_region pour faire le lien avec dim_geographie plus tard
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gold.stg_etablissements_raw (
                finess VARCHAR,
                nom VARCHAR,
                code_region VARCHAR 
            )
        """)
        
        # 2. Vider la table de staging avant le chargement (Idempotence)
        cur.execute("TRUNCATE TABLE gold.stg_etablissements_raw")
        
        # 3. Copie rapide via COPY depuis le fichier Bronze
        bronze_path = '/opt/airflow/data/bronze/etablissements_raw.csv'
        with open(bronze_path, 'r') as f:
            next(f) # Ignorer le header
            cur.copy_expert("COPY gold.stg_etablissements_raw FROM STDIN WITH CSV", f)
            
        conn.commit()
        print("Succès: Table de staging gold.stg_etablissements_raw chargée.")
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors du chargement staging : {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    load_staging_etablissements()