import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.test")

def get_env_variable(name: str):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing mandatory environment variable: '{name}'")
    return value

class EnvVariablesConfig:
    @property
    def database_url(self):
        return get_env_variable("DATABASE_URL")

    @property
    def secret_key(self):
        return get_env_variable("SECRET_KEY")

    @property
    def test_database_url(self):
        return get_env_variable("TEST_DATABASE_URL")

    @property
    def test_secret_key(self):
        return get_env_variable("TEST_SECRET_KEY")

env_vars  = EnvVariablesConfig()
