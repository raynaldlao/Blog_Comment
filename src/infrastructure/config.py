import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.test")


class InfraConfig:
    """
    Configuration manager for the infrastructure layer.

    Handles loading environment variables from .env and .env.test files
    to ensure total isolation from the legacy app/ configuration.
    """

    def _get_env(self, name: str) -> str:
        """
        Helper method to retrieve an environment variable.

        Args:
            name (str): The name of the environment variable to fetch.

        Returns:
            str: The value of the environment variable.

        Raises:
            RuntimeError: If the mandatory environment variable is missing.
        """
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"Infrastructure Error : Missing environment variable '{name}'")
        return value

    @property
    def database_url(self) -> str:
        """
        Retrieves the production database connection string.

        Returns:
            str: The PostgreSQL connection URL.
        """
        return self._get_env("DATABASE_URL")

    @property
    def test_database_url(self) -> str:
        """
        Retrieves the test database connection string.

        Returns:
            str: The PostgreSQL connection URL for testing.
        """
        return self._get_env("TEST_DATABASE_URL")


infra_config = InfraConfig()
