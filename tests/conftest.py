import pytest
from sqlalchemy import text

from app import initialize_flask_application
from app.models.account_model import Account
from app.models.article_model import Article
from app.models.comment_model import Comment
from config.configuration_variables import env_vars
from database.database_setup import Base, database_engine
from database.database_setup import db_session as app_db_session


def truncate_all_tables(connection):
    tables = Base.metadata.sorted_tables
    table_names = ", ".join(f'"{t.name}"' for t in tables)
    if table_names:
        connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))


@pytest.fixture(scope="function")
def app():
    flask_app = initialize_flask_application()
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": env_vars.test_secret_key
    })
    yield flask_app


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    # We include the 'app' fixture as a dependency to ensure that the Flask application
    # is fully initialized before the database session is established. This guarantees
    # that all configurations and model discoveries are completed

    # Explicitly referencing models to satisfy linters (prevent unused import errors)
    # Ensure SQLAlchemy's Base metadata is populated for TRUNCATE operations
    _ = (Account, Article, Comment)
    if database_engine.url.render_as_string(hide_password=False) != env_vars.test_database_url:
        pytest.exit("SECURITY ERROR: The current database URL does not match the configured TEST database URL.")

    app_db_session.remove()
    with database_engine.connect() as connection:
        truncate_all_tables(connection)
        connection.commit()

    try:
        yield app_db_session
    finally:
        app_db_session.rollback()
        app_db_session.remove()
