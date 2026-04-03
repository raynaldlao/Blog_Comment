from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.config import infra_config
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


class SqlAlchemyTestBase:
    """
    Shared Base class for SQLAlchemy integration tests.
    Connects to the PostgreSQL test database, creates tables before
    each test and truncates data after each test for inspection.
    """

    def setup_method(self):
        self.engine = create_engine(infra_config.test_database_url)
        SqlAlchemyModel.metadata.create_all(self.engine)

        with self.engine.connect() as connection:
            tables = SqlAlchemyModel.metadata.sorted_tables
            table_names = ", ".join(f'"{t.name}"' for t in tables)
            if table_names:
                from sqlalchemy import text
                connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))
                connection.commit()

        session_factory = sessionmaker(bind=self.engine)
        self.session = session_factory()

    def teardown_method(self):
        self.session.rollback()
        self.session.close()
        self.engine.dispose()
