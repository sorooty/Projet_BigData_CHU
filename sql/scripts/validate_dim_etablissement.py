import psycopg2
import os

def validate_etablissement():
    conn = psycopg2.connect(
        host='postgres',
        database='chu',
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin')
    )
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM gold.dim_etablissement")
    count = cur.fetchone()[0]
    
    conn.close()
    
    if count == 0:
        raise ValueError("Échec de la validation : la table gold.dim_etablissement est vide.")
    
    print(f"Validation réussie : {count} enregistrements dans gold.dim_etablissement.")

if __name__ == '__main__':
    validate_etablissement()