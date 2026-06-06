import psycopg2
import os

def load_staging_consultations():
    conn = psycopg2.connect(
        host='postgres',
        database='chu',
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin')
    )
    cur = conn.cursor()
    
    try:
        # Création de la table de staging temporaire
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gold.stg_consultations_raw (
                id_patient_src VARCHAR,
                date_consultation_src TIMESTAMP,
                code_diag_src VARCHAR,
                finess_src VARCHAR,
                id_prof_src VARCHAR,
                duree_consult_src INT
            )
        """)
        
        cur.execute("TRUNCATE TABLE gold.stg_consultations_raw")
        
        bronze_path = '/opt/airflow/data/bronze/consultations_raw.csv'
        with open(bronze_path, 'r') as f:
            next(f)  # Sauter l'en-tête
            cur.copy_expert("COPY gold.stg_consultations_raw FROM STDIN WITH CSV", f)
            
        conn.commit()
        print("Succès: Table de staging gold.stg_consultations_raw chargée.")
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur chargement staging consultations : {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    load_staging_consultations()