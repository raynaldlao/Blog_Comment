import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app import initialize_flask_application
from database.database_setup import Base, database_engine
from database.database_setup import db_session as app_db_session

SessionLocal = sessionmaker(bind=database_engine)


def truncate_all_tables(connection):
    tables = Base.metadata.sorted_tables
    table_names = ", ".join(f'"{t.name}"' for t in tables)
    if table_names:
        connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))


@pytest.fixture(scope="function")
def app():
    flask_app = initialize_flask_application()
    flask_app.config.update(
        {
            "TESTING": True,
        }
    )
    return flask_app


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db_session():
    with database_engine.connect() as connection:
        truncate_all_tables(connection)
        connection.commit()

    yield app_db_session
    app_db_session.remove()
