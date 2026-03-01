import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from config.configuration_variables import env_vars

"""
Database engine and session management.
"""

if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
    database_url: str = env_vars.test_database_url
else:
    database_url: str = env_vars.database_url

database_engine = create_engine(database_url)
session_factory = sessionmaker(bind=database_engine)
db_session = scoped_session(session_factory)
Base = declarative_base()
Base.query = db_session.query_property()
