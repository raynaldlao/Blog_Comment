from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from app.configuration_variables import ConfigurationVariables

database_engine  = create_engine(ConfigurationVariables.DATABASE_URL)
Base = declarative_base()
