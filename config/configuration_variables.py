import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.test")

def get_env_variable(name: str) -> str:
    """
    Retrieves an environment variable or raises a RuntimeError if missing.

    Args:
        name (str): The name of the environment variable.

    Returns:
        str: The value of the environment variable.

    Raises:
        RuntimeError: If the environment variable is not set.
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing mandatory environment variable: '{name}'")
    return value


class EnvVariablesConfig:
    """
    Configuration class to manage environment variables for the application.
    """

    @property
    def database_url(self) -> str:
        """
        The production database URL.

        Returns:
            str: Database connection string.
        """
        return get_env_variable("DATABASE_URL")

    @property
    def secret_key(self) -> str:
        """
        The secret key for Flask sessions.

        Returns:
            str: Secret key string.
        """
        return get_env_variable("SECRET_KEY")

    @property
    def test_database_url(self) -> str:
        """
        The test database URL.

        Returns:
            str: Test database connection string.
        """
        return get_env_variable("TEST_DATABASE_URL")

    @property
    def test_secret_key(self) -> str:
        """
        The secret key for Flask sessions during testing.

        Returns:
            str: Test secret key string.
        """
        return get_env_variable("TEST_SECRET_KEY")


env_vars = EnvVariablesConfig()
