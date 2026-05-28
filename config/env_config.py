import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.test")


class EnvConfig:
    """
    Configuration manager for environment variables.

    Handles loading environment variables from .env and .env.test files.
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

    @property
    def argon2_time_cost(self) -> int:
        """
        Retrieves the Argon2 time cost from environment.

        Returns:
            int: The Argon2 time cost.
        """
        return int(self._get_env("ARGON2_TIME_COST"))

    @property
    def argon2_memory_cost(self) -> int:
        """
        Retrieves the Argon2 memory cost from environment.

        Returns:
            int: The Argon2 memory cost in KiB.
        """
        return int(self._get_env("ARGON2_MEMORY_COST"))

    @property
    def argon2_parallelism(self) -> int:
        """
        Retrieves the Argon2 parallelism from environment.

        Returns:
            int: The Argon2 parallelism.
        """
        return int(self._get_env("ARGON2_PARALLELISM"))

    @property
    def test_argon2_time_cost(self) -> int:
        """
        Retrieves the test Argon2 time cost from environment.

        Returns:
            int: The Argon2 time cost for tests.
        """
        return int(self._get_env("TEST_ARGON2_TIME_COST"))

    @property
    def test_argon2_memory_cost(self) -> int:
        """
        Retrieves the test Argon2 memory cost from environment.

        Returns:
            int: The Argon2 memory cost in KiB for tests.
        """
        return int(self._get_env("TEST_ARGON2_MEMORY_COST"))

    @property
    def test_argon2_parallelism(self) -> int:
        """
        Retrieves the test Argon2 parallelism from environment.

        Returns:
            int: The Argon2 parallelism for tests.
        """
        return int(self._get_env("TEST_ARGON2_PARALLELISM"))


env_config = EnvConfig()
