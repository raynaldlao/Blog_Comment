import pytest
from sqlalchemy import create_engine

from src.infrastructure.config import infra_config
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


@pytest.fixture(scope="session")
def db_engine():
    """
    Session-scoped fixture that creates the SQLAlchemy engine and
    initializes the schema exactly once for the entire test run.
    """
    engine = create_engine(infra_config.test_database_url)
    SqlAlchemyModel.metadata.create_all(engine)
    yield engine
    engine.dispose()
