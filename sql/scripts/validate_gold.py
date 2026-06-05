"""
Validation qualite du slice consultations dans Gold.
"""

import logging

from utils import log_step, validate_table

logger = logging.getLogger(__name__)


def validate_gold() -> None:
    """Controle les tables attendues pour le pipeline consultations."""
    try:
        log_step("validate_gold", "starting")

        required_tables = [
            ("gold.stg_consultations_raw", {"min_rows": 1}),
            ("gold.dim_temps", {"min_rows": 1}),
            ("gold.dim_patient", {"min_rows": 1}),
            ("gold.dim_etablissement", {"min_rows": 1}),
            ("gold.dim_diagnostic", {"min_rows": 1}),
            ("gold.fait_consultation", {"min_rows": 1}),
        ]

        for table_name, checks in required_tables:
            validate_table(table_name, checks)

        log_step("validate_gold", "success", {"tables": len(required_tables)})

    except Exception as e:
        log_step("validate_gold", "failed", {"error": str(e)})
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validate_gold()
