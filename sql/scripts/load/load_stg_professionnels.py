import psycopg2
import os

def load_staging_professionnels():
    conn = psycopg2.connect(
        host='postgres',
        database='chu',
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin')
    )
    cur = conn.cursor()
    
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gold.stg_professionnels_raw (
                id_prof_source VARCHAR,
                nom_source VARCHAR
            )
        """)
        
        cur.execute("TRUNCATE TABLE gold.stg_professionnels_raw")
        
        bronze_path = '/opt/airflow/data/bronze/professionnels_raw.csv'
        with open(bronze_path, 'r') as f:
            next(f)  # Skip header
            cur.copy_expert("COPY gold.stg_professionnels_raw FROM STDIN WITH CSV", f)
            
        conn.commit()
        print("Succès: Table de staging gold.stg_professionnels_raw chargée.")
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur chargement staging professionnels : {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    load_staging_professionnels()