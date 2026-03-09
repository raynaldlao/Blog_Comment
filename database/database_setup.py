import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from config.configuration_variables import env_vars

"""
This module handles the database engine creation and scoped session management.
It uses an environment-based configuration to switch between production
and test databases.
"""

if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
    database_url: str = env_vars.test_database_url
else:
    database_url: str = env_vars.database_url

database_engine = create_engine(database_url)
session_factory = sessionmaker(bind=database_engine)
db_session = scoped_session(session_factory)


class Base(DeclarativeBase):
    """
    Native SQLAlchemy 2.0 declarative base class.
    All models should inherit from this class.
    """

    pass
