import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.core.config import load_settings
from src.core.db import session_scope
from src.core.security import pseudonymize
from src.etl.base import BaseEtlJob


logger = logging.getLogger(__name__)


class PilotSoinsJob(BaseEtlJob):
    """Job pilote pour valider le socle ETL sur la source consultations."""

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine, "pilot_soins")
        self.settings = load_settings()

    def execute(self) -> tuple[int, int]:
        # Enchaînement volontairement simple: check source, silver, puis gold.
        self._assert_source_table_exists()
        self._prepare_silver_table()
        rows_read = self._load_to_silver()
        rows_written = self._load_to_gold()
        return rows_read, rows_written

    def _assert_source_table_exists(self) -> None:
        with session_scope(self.engine) as session:
            table_exists = session.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'operational'
                          AND table_name = 'consultations'
                    )
                    """
                )
            ).scalar_one()
        if not table_exists:
            raise RuntimeError(
                "Table source absente: operational.consultations. "
                "Charger la source opérationnelle avant d'exécuter le job pilote."
            )

    def _prepare_silver_table(self) -> None:
        # Table intermédiaire propre avant chargement analytique.
        with session_scope(self.engine) as session:
            session.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS silver.consultations_clean (
                        consultation_source_id TEXT PRIMARY KEY,
                        date_consultation DATE NOT NULL,
                        etablissement_id TEXT,
                        diagnostic_code TEXT,
                        professionnel_id TEXT,
                        patient_hash TEXT NOT NULL,
                        duree_minutes INT
                    )
                    """
                )
            )

    def _load_to_silver(self) -> int:
        with session_scope(self.engine) as session:
            rows = session.execute(
                text(
                    """
                    SELECT
                        consultation_id::text AS consultation_source_id,
                        date_consultation::date AS date_consultation,
                        etablissement_id::text AS etablissement_id,
                        diagnostic_code::text AS diagnostic_code,
                        professionnel_id::text AS professionnel_id,
                        patient_id::text AS patient_id,
                        duree_minutes::int AS duree_minutes
                    FROM operational.consultations
                    """
                )
            ).mappings().all()

            # Pseudonymisation appliquée ici pour ne pas propager d'identifiant brut.
            silver_rows = [
                {
                    "consultation_source_id": row["consultation_source_id"],
                    "date_consultation": row["date_consultation"],
                    "etablissement_id": row["etablissement_id"],
                    "diagnostic_code": row["diagnostic_code"],
                    "professionnel_id": row["professionnel_id"],
                    "patient_hash": pseudonymize(row["patient_id"], self.settings.pseudonymization_key),
                    "duree_minutes": row["duree_minutes"],
                }
                for row in rows
            ]

            # On recharge la table clean entièrement pour ce pilote.
            session.execute(text("TRUNCATE TABLE silver.consultations_clean"))
            if silver_rows:
                session.execute(
                    text(
                        """
                        INSERT INTO silver.consultations_clean (
                            consultation_source_id,
                            date_consultation,
                            etablissement_id,
                            diagnostic_code,
                            professionnel_id,
                            patient_hash,
                            duree_minutes
                        )
                        VALUES (
                            :consultation_source_id,
                            :date_consultation,
                            :etablissement_id,
                            :diagnostic_code,
                            :professionnel_id,
                            :patient_hash,
                            :duree_minutes
                        )
                        """
                    ),
                    silver_rows,
                )
        logger.info("Silver consultations_clean chargée: %s lignes", len(rows))
        return len(rows)

    def _load_to_gold(self) -> int:
        # Chargement des dimensions minimales puis de la table de faits.
        with session_scope(self.engine) as session:
            session.execute(
                text(
                    """
                    INSERT INTO gold.dim_temps (date_key, annee, trimestre, mois, semaine)
                    SELECT DISTINCT
                        c.date_consultation AS date_key,
                        EXTRACT(YEAR FROM c.date_consultation)::int AS annee,
                        EXTRACT(QUARTER FROM c.date_consultation)::int AS trimestre,
                        EXTRACT(MONTH FROM c.date_consultation)::int AS mois,
                        EXTRACT(WEEK FROM c.date_consultation)::int AS semaine
                    FROM silver.consultations_clean c
                    ON CONFLICT (date_key) DO NOTHING
                    """
                )
            )
            session.execute(
                text(
                    """
                    INSERT INTO gold.dim_etablissement (etablissement_id)
                    SELECT DISTINCT c.etablissement_id
                    FROM silver.consultations_clean c
                    WHERE c.etablissement_id IS NOT NULL
                    ON CONFLICT (etablissement_id) DO NOTHING
                    """
                )
            )
            session.execute(text("TRUNCATE TABLE gold.fait_consultation RESTART IDENTITY"))
            inserted = session.execute(
                text(
                    """
                    INSERT INTO gold.fait_consultation (
                        consultation_source_id,
                        date_key,
                        etablissement_id,
                        diagnostic_code,
                        professionnel_id,
                        patient_hash,
                        nb_consultations,
                        duree_minutes
                    )
                    SELECT
                        c.consultation_source_id,
                        c.date_consultation AS date_key,
                        c.etablissement_id,
                        c.diagnostic_code,
                        c.professionnel_id,
                        c.patient_hash,
                        1 AS nb_consultations,
                        c.duree_minutes
                    FROM silver.consultations_clean c
                    RETURNING consultation_id
                    """
                )
            ).all()
        logger.info("Gold fait_consultation chargée: %s lignes", len(inserted))
        return len(inserted)
