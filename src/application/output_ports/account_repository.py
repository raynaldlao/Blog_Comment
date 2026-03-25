from abc import ABC, abstractmethod

from src.application.domain.account import Account


class AccountRepository(ABC):
    """
    Output port defining the contract for Account persistence operations.
    Any infrastructure adapter (SQLAlchemy, MongoDB, etc.) must implement
    this interface.
    """

    @abstractmethod
    def find_by_username(self, username: str) -> Account | None:
        """
        Retrieves an account by its username.

        Args:
            username (str): The username to search for.

        Returns:
            Account | None: The Account domain entity if found,
            None otherwise.
        """
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Account | None:
        """
        Retrieves an account by its email address.

        Args:
            email (str): The email address to search for.

        Returns:
            Account | None: The Account domain entity if found,
            None otherwise.
        """
        pass

    @abstractmethod
    def save(self, account: Account) -> None:
        """
        Saves a new account to the database.

        Args:
            account (Account): The Account domain entity to save.
        """
        pass
