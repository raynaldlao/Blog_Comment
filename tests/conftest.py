from typing import Any, Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from app import initialize_flask_application
from app.models.account_model import Account
from app.models.article_model import Article
from app.models.comment_model import Comment
from config.configuration_variables import env_vars
from database.database_setup import Base, database_engine
from database.database_setup import db_session as app_db_session


def truncate_all_tables(connection: Connection) -> None:
    """
    Truncates all tables in the database to ensure a clean state for tests.

    Args:
        connection (Connection): SQLAlchemy connection object.
    """
    tables = Base.metadata.sorted_tables
    table_names = ", ".join(f'"{t.name}"' for t in tables)
    if table_names:
        connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))


@pytest.fixture(scope="function")
def app() -> Generator[Flask, Any, None]:
    """
    Pytest fixture that initializes the Flask application for testing.

    Yields:
        Flask: The Flask application instance.
    """
    flask_app = initialize_flask_application()
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": env_vars.test_secret_key
    })
    yield flask_app


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """
    Pytest fixture that provides a test client for the Flask application.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        FlaskClient: A test client.
    """
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app: Flask) -> Generator[Session, Any, None]:
    """
    Pytest fixture that provides a clean database session for each test function.
    Truncates all tables before yielding the session.

    Args:
        app (Flask): The Flask application instance.

    Yields:
        Session: A scoped SQLAlchemy session.
    """
    # Explicitly referencing models to satisfy linters and ensure metadata is populated
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
