import os

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Base

file_env = dotenv_values(".env.test")

# Database selection logic:
# 1. Local environment: use TEST_DATABASE_URL from .env.test
# 2. Optional override: use TEST_DATABASE_URL from os.environ if provided
database_url = (
    file_env.get("TEST_DATABASE_URL")
    or os.getenv("TEST_DATABASE_URL")
)

engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)

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
