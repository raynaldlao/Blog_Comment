import os

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.controllers.login as login_controller
import app.database as app_database
from app import initialize_flask_application
from app.models import Account, Article, Base, Comment

file_env = dotenv_values(".env.test")

def get_required_env_test(value, name):
    if not value:
        raise OSError(f"Missing required environment variable '{name}' in .env.test file.")
    return value

class ConfigurationVariablesTest:
    DATABASE_URL = get_required_env_test(
        file_env.get("TEST_DATABASE_URL") or os.getenv("TEST_DATABASE_URL"), 
        "TEST_DATABASE_URL"
    )
    SECRET_KEY = get_required_env_test(
        file_env.get("TEST_SECRET_KEY") or os.getenv("TEST_SECRET_KEY"), 
        "TEST_SECRET_KEY"
    )

engine = create_engine(ConfigurationVariablesTest.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def account_model():
    return Account

def article_model():
    return Article

def comment_model():
    return Comment

def truncate_all_tables(connection):
    tables = Base.metadata.sorted_tables
    table_names = ", ".join(f'"{t.name}"' for t in tables)
    if table_names:
        connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))

@pytest.fixture(scope="function")
def app(monkeypatch):
    flask_app = initialize_flask_application()
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": ConfigurationVariablesTest.SECRET_KEY,
    })

    monkeypatch.setattr(app_database, "database_engine", engine)
    monkeypatch.setattr(login_controller, "database_engine", engine)

    return flask_app

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

@pytest.fixture(scope="function")
def db_session():
    with engine.connect() as connection:
        truncate_all_tables(connection)
        connection.commit()

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
