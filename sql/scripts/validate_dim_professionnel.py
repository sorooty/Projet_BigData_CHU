import psycopg2
import os

def validate_professionnel():
    conn = psycopg2.connect(
        host='postgres',
        database='chu',
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin')
    )
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM gold.dim_professionnel")
    count = cur.fetchone()[0]
    conn.close()
    
    if count == 0:
        raise ValueError("Erreur : La table gold.dim_professionnel n'a pas été alimentée.")
        
    print(f"Validation réussie : {count} professionnels disponibles dans la dimension Gold.")

if __name__ == '__main__':
    validate_professionnel()