from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.core.config import load_settings


def get_engine() -> Engine:
    # Moteur SQLAlchemy partagé par tous les jobs.
    settings = load_settings()
    return create_engine(settings.sqlalchemy_url, future=True)


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    # Contexte standard pour éviter les commits oubliés.
    # Commit auto si tout va bien, rollback sinon.
    session = Session(bind=engine, future=True)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
