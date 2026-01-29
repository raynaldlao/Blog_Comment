import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

# This variable must be added to the .env file for it to work
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
