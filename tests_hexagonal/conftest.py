import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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
    session_factory = sessionmaker(bind=db_engine)
    session = scoped_session(session_factory)
    truncate_all_tables(session)
    yield session
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
