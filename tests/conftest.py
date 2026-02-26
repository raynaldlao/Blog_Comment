import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app import initialize_flask_application
from app.models.account_model import Account
from app.models.article_model import Article
from app.models.comment_model import Comment
from configurations.configuration_variables import env_vars
from database.database_setup import Base, database_engine

SessionLocal = sessionmaker(bind=database_engine)

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
def app():
    flask_app = initialize_flask_application()
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": env_vars.test_secret_key
    })
    return flask_app

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

@pytest.fixture(scope="function")
def db_session():
    with database_engine.connect() as connection:
        truncate_all_tables(connection)
        connection.commit()

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
