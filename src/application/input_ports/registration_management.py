from abc import ABC, abstractmethod

from src.application.domain.account import Account


class RegistrationManagementPort(ABC):
    """
    Input port (interface) defining the business operations for user registration.
    """

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
