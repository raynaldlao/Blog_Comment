import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from config.env_config import env_config

"""
Infrastructure-specific database configuration and session management.

This module initializes the SQLAlchemy engine and provides a scoped session
factory for the hexagonal architecture, ensuring isolation from the legacy
database setup. It automatically switches between production and test databases.
"""

if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
    db_url = env_config.test_database_url
else:
    db_url = env_config.database_url

sqlalchemy_engine = create_engine(db_url)
sqlalchemy_session_factory = sessionmaker(bind=sqlalchemy_engine)
sqlalchemy_db_session = scoped_session(sqlalchemy_session_factory)
