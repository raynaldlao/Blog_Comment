from abc import ABC, abstractmethod

from src.application.domain.account import Account


class LoginManagementPort(ABC):
    """
    Input port (interface) defining the business operations for user authentication.
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
