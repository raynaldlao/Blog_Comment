from typing import cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from blog_comment_application import create_app
from src.infrastructure.config import infra_config
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel
from tests_hexagonal.db_utils import truncate_all_tables


@pytest.fixture(scope="session")
def db_engine():
    """Permanent engine for the test session."""
    engine = create_engine(infra_config.test_database_url)
    return engine

@pytest.fixture(scope="session")
def db_setup(db_engine):
    """Ensures all tables are created once per session."""
    SqlAlchemyModel.metadata.create_all(db_engine)
    yield

@pytest.fixture(scope="function")
def db_session(db_engine, db_setup):
    """
    Creates a new, clean SQLAlchemy scoped session for each test.
    Automatically truncates all tables before yielding to ensure test isolation.
    """
    session_factory = sessionmaker(bind=db_engine)
    session = scoped_session(session_factory)
    mapped_session = cast(Session, session)
    truncate_all_tables(mapped_session)
    yield mapped_session
    session.remove()

@pytest.fixture(scope="function")
def app_with_db(db_session):
    """
    Creates a Flask app instance injected with the test database session.
    """
    app = create_app(db_session=db_session)
    app.config["TESTING"] = True

    return app

@pytest.fixture(scope="function")
def client(app_with_db):
    """A Flask test client."""
    return app_with_db.test_client()
