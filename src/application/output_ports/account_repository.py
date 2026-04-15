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
    def get_by_id(self, account_id: int) -> Account | None:
        """
        Retrieves a single account by its ID.

        Args:
            account_id (int): The unique identifier of the account.

        Returns:
            Account | None: The Account domain entity if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_by_ids(self, account_ids: list[int]) -> list[Account]:
        """
        Retrieves a list of accounts by their unique IDs in a single batch.

        Args:
            account_ids (list[int]): A list of account identifiers.

        Returns:
            list[Account]: A list of found Account domain entities.
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
