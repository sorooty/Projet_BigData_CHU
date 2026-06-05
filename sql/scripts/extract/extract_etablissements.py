import pandas as pd
from pathlib import Path
import sys

def extract_etablissements():
    try:
        # Chemin du fichier source (à adapter selon le point de montage de Seyni)
        input_file = Path('/data/raw/etablissements.csv')
        output_file = Path('/opt/airflow/data/bronze/etablissements_raw.csv')
        
        # Lecture (on suppose un séparateur point-virgule, très courant pour les CSV FR)
        df = pd.read_csv(input_file, sep=';')
        
        # Règle Bronze : Nettoyage critique uniquement. La clé primaire finess ne peut pas être nulle.
        df = df.dropna(subset=['finess'])
        
        # Sauvegarde en Bronze
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"Succès: {len(df)} établissements extraits vers Bronze.")
        
    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        raise

if __name__ == '__main__':
    extract_etablissements()