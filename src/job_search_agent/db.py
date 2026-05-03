"""Database engine and session factory for the job-search-agent SQLite store."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from job_search_agent.models import Base

_DEFAULT_DB_PATH = Path("jobs.db")


def get_engine(db_path: Path | str = _DEFAULT_DB_PATH) -> Engine:
    """Return a SQLAlchemy engine connected to the SQLite file at *db_path*.

    Pass ``":memory:"`` for an in-memory database (useful in tests).
    """
    url = f"sqlite:///{db_path}"
    return create_engine(url, echo=False)


def init_db(engine: Engine) -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(engine)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a bound sessionmaker for the given engine."""
    return sessionmaker(bind=engine)
