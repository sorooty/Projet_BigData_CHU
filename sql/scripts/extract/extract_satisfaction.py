# Extract - Satisfaction
## Purpose: Load Satisfaction data into bronze schema

import pandas as pd
import psycopg2
import logging
import chardet
import glob
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'postgres',
    'database': 'chu_data',
    'user': 'chu_admin',
    'password': '123456789',
    'port': 5432
}

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def read_csv_safe(file_path):
    encoding = detect_encoding(file_path)
    logger.info(f"Detected encoding: {encoding}")
    
    encodings = [encoding, 'latin-1', 'iso-8859-1', 'cp1252', 'utf-8']
    
    for enc in encodings:
        try:
            df = pd.read_csv(
                file_path, 
                encoding=enc, 
                low_memory=False,
                nrows=10000,
                on_bad_lines='skip',
                engine='c',
                sep=';' if 'ESATIS' in file_path else ','
            )
            logger.info(f"✓ Read {len(df)} rows with {enc}")
            return df
        except Exception as e:
            logger.debug(f"Failed with {enc}")
            continue
    
    return None

def extract_satisfaction():
    csv_pattern = "/opt/airflow/data/raw/raw/raw/Satisfaction_*_donnees.csv"
    csv_files = sorted(glob.glob(csv_pattern))
    
    try:
        logger.info("="*60)
        logger.info("EXTRACT SATISFACTION")
        logger.info("="*60)
        logger.info(f"Found {len(csv_files)} files")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            DROP TABLE IF EXISTS bronze.satisfaction_raw CASCADE;
            CREATE TABLE bronze.satisfaction_raw (
                id SERIAL PRIMARY KEY,
                finess VARCHAR,
                annee INT,
                score FLOAT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        logger.info("Table created")
        
        total_inserted = 0
        
        for csv_file in csv_files:
            try:
                logger.info(f"\nProcessing: {csv_file.split('/')[-1]}")
                
                df = read_csv_safe(csv_file)
                if df is None or len(df) == 0:
                    logger.warning(f"  Skipped (empty or unreadable)")
                    continue
                
                logger.info(f"  Columns: {list(df.columns)[:5]}...")
                
                year_match = re.search(r'(20\d{2})', csv_file)
                year = int(year_match.group(1)) if year_match else 2020
                
                inserted = 0
                for idx, row in df.iterrows():
                    try:
                        finess = row.get('finess', None)
                        
                        # Try numeric columns for score
                        score = None
                        for col in ['tda_c_etbt', 'trd_c_etbt', 'dec_c_etbt', 'dtn_c_etbt', 'tdp_c_etbt', 'tre_c_etbt', 'score_all_rea_ajust']:
                            if col in df.columns and pd.notna(row[col]):
                                try:
                                    val = float(row[col])
                                    if 0 <= val <= 100:
                                        score = val
                                        break
                                except:
                                    pass
                        
                        if finess and score is not None:
                            cur.execute(
                                "INSERT INTO bronze.satisfaction_raw (finess, annee, score) VALUES (%s, %s, %s)",
                                (str(finess), year, score)
                            )
                            inserted += 1
                    except Exception as e:
                        pass
                
                conn.commit()
                logger.info(f"  ✓ Inserted {inserted} rows")
                total_inserted += inserted
                
            except Exception as e:
                logger.warning(f"  Error: {str(e)}")
                continue
        
        cur.execute("SELECT COUNT(*) FROM bronze.satisfaction_raw")
        count = cur.fetchone()[0]
        logger.info(f"\n✓ Total rows in bronze: {count}")
        
        cur.close()
        conn.close()
        logger.info("✓ EXTRACT SATISFACTION COMPLETE\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    extract_satisfaction()
