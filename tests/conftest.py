import os

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Account, Article, Base, Comment

file_env = dotenv_values(".env.test")
# CI (GitHub Actions) provides TEST_DATABASE_URL via environment variables.
# Locally, we fall back to .env.test for a dedicated test database.
# load_dotenv() won't work if we use ".env.test"
# This keeps the test configuration consistent across environments without changing the code.
database_url = file_env.get("TEST_DATABASE_URL") or os.getenv("TEST_DATABASE_URL")
engine = create_engine(database_url)
SessionLocal = sessionmaker()

def account_model():
    return Account

def article_model():
    return Article

def comment_model():
    return Comment

def truncate_all_tables(connection):
    tables = Base.metadata.sorted_tables
    table_names = ", ".join(f'"{t.name}"' for t in tables)
    connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))

@pytest.fixture(scope="function")
def db_session():
    with engine.begin() as connection:
        truncate_all_tables(connection)
        session = SessionLocal(bind=connection)
        try:
            yield session
        finally:
            session.close()
