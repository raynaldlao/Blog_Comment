from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.env_config import env_config


def setup_database(db_session: Session | None = None) -> Session:
    """
    Initializes the database connection and session.

    Args:
        db_session: Optional existing SQLAlchemy session (e.g., for testing).

    Returns:
        Session: A configured SQLAlchemy database session.
    """
    if db_session is None:
        engine = create_engine(env_config.database_url)
        session_factory = sessionmaker(bind=engine)
        db_session = session_factory()
    return db_session
