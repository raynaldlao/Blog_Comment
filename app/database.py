import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# This variable must be added to the .env file for it to work
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))