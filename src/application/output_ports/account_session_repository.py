from abc import ABC, abstractmethod


class AccountSessionRepository(ABC):
    """
    Interface for persistence of session data.

    This encapsulates how session information is physically stored,
    allowing the application to remain decoupled from infrastructure details.
    By specifying native types (str, int, etc.), it ensures that only
    serializable primitives cross the boundary.
    """

    @abstractmethod
    def store_value(self, key: str, value: str | int | float | bool | dict | list) -> None:
        """
        Stores a primitive value in the current session.

        Args:
            key (str): The string identifier for the session variable.
            value (str | int | float | bool | dict | list): The primitive data to store.
        """
        pass

    @abstractmethod
    def retrieve_value(self, key: str) -> str | int | float | bool | dict | list | None:
        """
        Retrieves a primitive value from the current session.

        Args:
            key (str): The string identifier for the session variable.

        Returns:
            str | int | float | bool | dict | list | None: The stored data if found, otherwise None.
        """
        pass

    @abstractmethod
    def invalidate(self) -> None:
        """
        Wipes all current session data from storage.
        """
        pass
