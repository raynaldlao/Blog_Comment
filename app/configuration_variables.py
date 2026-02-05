import os

from dotenv import load_dotenv

load_dotenv()

def get_required_env(name):
    value = os.getenv(name)
    if not value:
        if os.getenv("TEST_DATABASE_URL") or os.getenv("PYTEST_CURRENT_TEST"):
            if name == "DATABASE_URL":
                return "postgresql://user:pass@localhost/dummy"
            return "dummy_secret_key"

        raise OSError(f"Missing required environment variable '{name}' in .env file.")
    return value

class ConfigurationVariables:
    DATABASE_URL = get_required_env("DATABASE_URL")
    SECRET_KEY = get_required_env("SECRET_KEY")
