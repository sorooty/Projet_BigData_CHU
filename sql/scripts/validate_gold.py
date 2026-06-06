# Data Quality Validation
## Purpose: Validate gold schema tables for data completeness and integrity

import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_gold():
    """Run quality checks on gold schema"""
    
    db_config = {
        'host': 'postgres',
        'database': 'chu_data',
        'user': 'chu_admin',
        'password': '123456789',
        'port': 5432
    }
    
    checks = {
        'dim_geographie': {
            'min_rows': 1,
            'query': 'SELECT COUNT(*) FROM gold.dim_geographie WHERE id_geo IS NOT NULL'
        },
        'fait_satisfaction': {
            'min_rows': 1,
            'query': 'SELECT COUNT(*) FROM gold.fait_satisfaction WHERE id_fait_satisfaction IS NOT NULL'
        },
        'fait_deces': {
            'min_rows': 1,
            'query': 'SELECT COUNT(*) FROM gold.fait_deces WHERE id_fait_deces IS NOT NULL'
        }
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        logger.info("Starting data quality validation...")
        all_passed = True
        
        for table_name, check_config in checks.items():
            cur.execute(check_config['query'])
            count = cur.fetchone()[0]
            min_rows = check_config['min_rows']
            
            if count >= min_rows:
                logger.info(f"✓ {table_name}: {count} rows (OK)")
            else:
                logger.warning(f"✗ {table_name}: {count} rows (FAIL - expected >= {min_rows})")
                all_passed = False
        
        # TODO: Add more validations
        # - Check for NULL values in critical columns
        # - Check for duplicate keys
        # - Check foreign key constraints
        
        cur.close()
        conn.close()
        
        if all_passed:
            logger.info("All validations PASSED")
        else:
            logger.warning("Some validations FAILED")
            raise Exception("Data quality validation failed")
            
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        raise

if __name__ == "__main__":
    validate_gold()
