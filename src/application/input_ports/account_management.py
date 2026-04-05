from abc import ABC, abstractmethod

from src.application.domain.account import Account


class AccountManagementPort(ABC):
    """
    Input port (interface) defining the business operations for account management.
    This serves as the API for the Core, to be used by input adapters (Web, CLI, etc.).
    """

    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Account | None:
        """
        Validates the user's credentials.

        Args:
            username (str): The username provided by the user.
            password (str): The plaintext password provided by the user.

        Returns:
            Account | None: The authenticated Account instance if
            credentials match, None otherwise.
        """
        pass

    @abstractmethod
    def create_account(self, username: str, password: str, email: str) -> Account | str:
        """
        Creates a new user account.

        Args:
            username (str): The username for the new account.
            password (str): The plaintext password for the new account.
            email (str): The email address for the new account.

        Returns:
            Account | str: The newly created Account domain entity, or an
            error message string if creation fails.
        """
        pass
