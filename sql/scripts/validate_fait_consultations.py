import psycopg2
import os

def validate_fait_consultations():
    conn = psycopg2.connect(
        host='postgres',
        database='chu',
        user=os.getenv('POSTGRES_USER', 'admin'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin')
    )
    cur = conn.cursor()
    
    # 1. Vérification du remplissage
    cur.execute("SELECT COUNT(*) FROM gold.fait_consultation")
    count_facts = cur.fetchone()[0]
    
    # 2. Vérification de la perte de lignes (Staging vs Faits)
    cur.execute("SELECT COUNT(*) FROM gold.stg_consultations_raw")
    count_staging = cur.fetchone()[0]
    
    conn.close()
    
    if count_facts == 0:
        raise ValueError("Erreur : La table de faits gold.fait_consultation est vide !")
        
    print(f"Validation réussie : {count_facts} actes de consultation insérés dans le modèle Gold.")
    print(f"Taux d'intégration : {(count_facts / count_staging) * 100:.2f}% des données sources intégrées.")

if __name__ == '__main__':
    validate_fait_consultations()