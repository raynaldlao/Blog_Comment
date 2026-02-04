import os

from dotenv import load_dotenv

load_dotenv()

def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise OSError(f"Missing required environment variable '{name}' in .env file.")
    return value

class ConfigurationVariables:
    DATABASE_URL = get_required_env("DATABASE_URL")
    SECRET_KEY = get_required_env("SECRET_KEY")
