# Load - Fait Décès
## Purpose: Final validation and load into gold.fait_deces

import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_fait_deces():
    """Validate and load mortality facts"""
    
    db_config = {
        'host': 'postgres',
        'database': 'chu_data',
        'user': 'chu_admin',
        'password': '123456789',
        'port': 5432
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Run transform SQL
        logger.info("Running transform_fait_deces.sql...")
        with open('/opt/airflow/sql/scripts/transform/transform_fait_deces.sql', 'r') as f:
            sql = f.read()
        
        cur.execute(sql)
        conn.commit()
        
        # Validation
        cur.execute("SELECT COUNT(*) FROM gold.fait_deces")
        count = cur.fetchone()[0]
        logger.info(f"Loaded {count} rows into gold.fait_deces")
        
        if count == 0:
            logger.warning("WARNING: No rows loaded!")
        
        cur.close()
        conn.close()
        logger.info("Load completed successfully")
        
    except Exception as e:
        logger.error(f"Error during load: {str(e)}")
        raise

if __name__ == "__main__":
    load_fait_deces()
