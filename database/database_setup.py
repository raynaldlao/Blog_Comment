import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from configurations.configuration_variables import env_vars

if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
    database_url = env_vars.test_database_url
else:
    database_url = env_vars.database_url

database_engine = create_engine(database_url)
Base = declarative_base()
