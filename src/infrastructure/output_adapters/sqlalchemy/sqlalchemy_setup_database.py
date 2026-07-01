import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.env_config import env_config


def setup_database(db_session: Session | None = None) -> Session:
    """Initialize database engine and return a configured SQLAlchemy session.

    Args:
        db_session: Optional pre-existing session for dependency injection
            (used in tests to inject a mock or transaction-bound session).

    Returns:
        Session: A configured SQLAlchemy database session connected to the engine.
    """
    if db_session is None:
        db_url = env_config.test_database_url if os.getenv("FLASK_ENV") == "test" else env_config.database_url
        engine = create_engine(db_url)
        session_factory = sessionmaker(bind=engine)
        db_session = session_factory()
    return db_session
