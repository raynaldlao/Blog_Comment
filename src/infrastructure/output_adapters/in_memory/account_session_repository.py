from typing import Any

from src.application.output_ports.account_session_repository import AccountSessionRepository


class InMemoryAccountSessionRepository(AccountSessionRepository):
    """
    In-memory implementation of AccountSessionRepository, useful for testing
    authentication services without requiring a web framework context (like Flask).
    """

    def __init__(self):
        """
        Initializes an empty session data dictionary.
        """
        self._session_data: dict[str, Any] = {}

    def store_value(self, key: str, value: str | int | float | bool | dict | list) -> None:
        """
        Assigns a primitive value to a session key using a local dictionary.

        Args:
            key (str): Identifier for the storage key.
            value (str | int | float | bool | dict | list): Data to store.
        """
        self._session_data[key] = value

    def retrieve_value(self, key: str) -> str | int | float | bool | dict | list | None:
        """
        Gets a value from a session key from the local dictionary.

        Args:
            key (str): Identifier for the storage key.

        Returns:
            str | int | float | bool | dict | list | None: The stored data or None.
        """
        return self._session_data.get(key)

    def invalidate(self) -> None:
        """
        Wipes the entire internal session dictionary.
        """
        self._session_data.clear()
