from abc import ABC, abstractmethod
import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.core.db import session_scope


logger = logging.getLogger(__name__)


class BaseEtlJob(ABC):
    """Classe de base commune pour tous les jobs ETL."""

    def __init__(self, engine: Engine, job_name: str) -> None:
        self.engine = engine
        self.job_name = job_name

    def run(self) -> None:
        # Pipeline standard: start log, exécution métier, end log.
        run_id = self._start_run()
        try:
            rows_read, rows_written = self.execute()
            self._end_run(run_id, "success", rows_read, rows_written, None)
            logger.info("Job %s terminé: read=%s write=%s", self.job_name, rows_read, rows_written)
        except Exception as exc:
            self._end_run(run_id, "failed", 0, 0, str(exc))
            logger.exception("Job %s en échec", self.job_name)
            raise

    @abstractmethod
    def execute(self) -> tuple[int, int]:
        # Chaque job doit retourner (rows_read, rows_written).
        raise NotImplementedError

    def _start_run(self) -> int:
        with session_scope(self.engine) as session:
            run_id = session.execute(
                text(
                    """
                    INSERT INTO audit.etl_run_log (job_name, status)
                    VALUES (:job_name, 'running')
                    RETURNING run_id
                    """
                ),
                {"job_name": self.job_name},
            ).scalar_one()
        return int(run_id)

    def _end_run(
        self,
        run_id: int,
        status: str,
        rows_read: int,
        rows_written: int,
        message: str | None,
    ) -> None:
        with session_scope(self.engine) as session:
            session.execute(
                text(
                    """
                    UPDATE audit.etl_run_log
                    SET ended_at = NOW(),
                        status = :status,
                        rows_read = :rows_read,
                        rows_written = :rows_written,
                        message = :message
                    WHERE run_id = :run_id
                    """
                ),
                {
                    "run_id": run_id,
                    "status": status,
                    "rows_read": rows_read,
                    "rows_written": rows_written,
                    "message": message,
                },
            )
