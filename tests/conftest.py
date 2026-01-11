import os

# ❌ Erreurs de lint ajoutées : imports inutilisés
import json
import math
import datetime

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine
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

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
