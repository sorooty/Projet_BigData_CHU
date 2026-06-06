# Extract - Décès en France
## Purpose: Load DECES_EN_FRANCE data into bronze schema

import pandas as pd
import psycopg2
import logging
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'postgres',
    'database': 'chu_data',
    'user': 'chu_admin',
    'password': '123456789',
    'port': 5432
}

def extract_deces():
    """Extract décès data from CSV to bronze.deces_raw"""
    
    csv_file = "/opt/airflow/data/raw/raw/raw/DECES_EN_FRANCE_deces.csv"
    
    try:
        logger.info("="*60)
        logger.info("EXTRACT DECES")
        logger.info("="*60)
        
        # Read CSV
        logger.info(f"Reading CSV: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False, nrows=5000)
        logger.info(f"Loaded {len(df)} rows")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Create table
        logger.info("Creating table bronze.deces_raw...")
        cur.execute("""
            DROP TABLE IF EXISTS bronze.deces_raw CASCADE;
            CREATE TABLE bronze.deces_raw (
                id SERIAL PRIMARY KEY,
                sexe VARCHAR,
                date_deces VARCHAR,
                code_lieu_deces VARCHAR,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        logger.info("Table created")
        
        # Insert data - MAP THE ACTUAL COLUMNS
        logger.info("Inserting data...")
        inserted = 0
        for idx, row in df.iterrows():
            try:
                sexe = row.get('sexe', None)
                date_deces = row.get('date_deces', None)
                code_lieu = row.get('code_lieu_deces', None)
                
                cur.execute(
                    "INSERT INTO bronze.deces_raw (sexe, date_deces, code_lieu_deces) VALUES (%s, %s, %s)",
                    (sexe, date_deces, code_lieu)
                )
                inserted += 1
            except Exception as e:
                logger.debug(f"Row {idx} error: {str(e)}")
                continue
        
        conn.commit()
        logger.info(f"Inserted {inserted} rows")
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM bronze.deces_raw WHERE sexe IS NOT NULL")
        count = cur.fetchone()[0]
        logger.info(f"✓ Rows with data: {count}")
        
        cur.close()
        conn.close()
        logger.info("✓ EXTRACT DECES COMPLETE\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    extract_deces()
