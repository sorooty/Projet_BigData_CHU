# STEP 3: EXTRACT GEOGRAPHIE
## Extract regions from deces data

import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'postgres',
    'database': 'chu_data',
    'user': 'chu_admin',
    'password': '123456789',
    'port': 5432
}

def run():
    logger.info("Extracting geography from deces data...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Create bronze geographie table from deces code_lieu_deces
    cur.execute("""
        DROP TABLE IF EXISTS bronze.geographie_raw CASCADE;
        CREATE TABLE bronze.geographie_raw (
            id SERIAL PRIMARY KEY,
            code_region VARCHAR,
            libelle_region VARCHAR,
            pays VARCHAR
        );
    """)
    conn.commit()
    logger.info("Table bronze.geographie_raw created")
    
    # Extract unique regions from deces (extract first 2 digits = region code)
    cur.execute("""
        INSERT INTO bronze.geographie_raw (code_region, libelle_region, pays)
        SELECT DISTINCT
            SUBSTRING(code_lieu_deces, 1, 2) as code_region,
            'Region_' || SUBSTRING(code_lieu_deces, 1, 2) as libelle_region,
            'France' as pays
        FROM bronze.deces_raw
        WHERE code_lieu_deces IS NOT NULL
          AND code_lieu_deces != ''
        ORDER BY code_region;
    """)
    conn.commit()
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM bronze.geographie_raw")
    count = cur.fetchone()[0]
    logger.info(f"✓ Extracted {count} unique regions")
    
    # Transform to gold.dim_geographie
    cur.execute("""
        TRUNCATE TABLE gold.dim_geographie CASCADE;
        
        INSERT INTO gold.dim_geographie (id_geo, code_region, libelle_region, pays)
        SELECT 
            ROW_NUMBER() OVER (ORDER BY code_region) as id_geo,
            code_region,
            libelle_region,
            pays
        FROM bronze.geographie_raw;
    """)
    conn.commit()
    
    # Verify final
    cur.execute("SELECT COUNT(*) FROM gold.dim_geographie")
    count = cur.fetchone()[0]
    logger.info(f"✓ Loaded {count} regions to gold.dim_geographie")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    run()
