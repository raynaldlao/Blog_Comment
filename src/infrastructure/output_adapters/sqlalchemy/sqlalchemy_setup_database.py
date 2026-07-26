from typing import cast

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from config.env_config import env_config


def setup_database(db_session: Session | None = None) -> Session:
    """Initialize database engine and return a thread-safe scoped session.

    Uses ``scoped_session`` to provide one session per thread, preventing
    cross-request transaction leaks. API-compatible with plain Session,
    so no changes are needed in downstream SQL adapters.

    When a test session is provided via ``db_session``, it is returned
    as-is (no scoping applied).

    Args:
        db_session: Optional pre-existing session for dependency injection
            (used in tests to inject a mock or transaction-bound session).

    Returns:
        Session: A configured scoped session when no test session is
        provided, or the injected session otherwise. The returned value
        is API-compatible with ``sqlalchemy.orm.Session``.
    """
    if db_session is not None:
        return db_session
    db_url = env_config.test_database_url if env_config.flask_env == "test" else env_config.database_url
    engine = create_engine(db_url)
    return cast(Session, scoped_session(sessionmaker(bind=engine)))
