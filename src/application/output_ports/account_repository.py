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

    @abstractmethod
    def update_avatar(self, account_id: int, avatar_file_id: str | None) -> None:
        """
        Updates the avatar_file_id for a given account.

        Args:
            account_id: The ID of the account to update.
            avatar_file_id: The new avatar file UUID, or None to remove.
        """
        pass

    @abstractmethod
    def update_email(self, account_id: int, new_email: str) -> None:
        """
        Updates the email address for a given account.

        Args:
            account_id: The ID of the account to update.
            new_email: The new email address to set.

        Raises:
            AccountAlreadyExistsError: If the new email is already taken
                by another account (detected at the database level).
        """
        pass

    @abstractmethod
    def update_password(self, account_id: int, new_hashed_password: str) -> None:
        """
        Updates the password hash for a given account.

        Args:
            account_id: The ID of the account to update.
            new_hashed_password: The new Argon2 hash to store.
        """
        pass

    @abstractmethod
    def update_role(self, account_id: int, new_role: str) -> None:
        """
        Updates the account_role for a given account.

        Args:
            account_id: The ID of the account to update.
            new_role: The new role string ("user" or "author").
        """
        pass

    @abstractmethod
    def get_all(self) -> list[Account]:
        """
        Retrieves all accounts from the data store.

        Returns:
            list[Account]: A list of all Account domain entities.
        """
        pass

    @abstractmethod
    def get_all_paginated(self, page: int = 1, per_page: int = 20) -> list[Account]:
        """
        Retrieves a paginated list of accounts, ordered by creation date descending.

        Args:
            page: The page number (1-indexed). Defaults to 1.
            per_page: The number of items per page. Defaults to 20.

        Returns:
            list[Account]: A list of Account domain entities for the given page.
        """
        pass

    @abstractmethod
    def count_all(self) -> int:
        """
        Returns the total number of accounts in the data store.

        Returns:
            int: The total count of accounts.
        """
        pass

    @abstractmethod
    def search(self, query: str, page: int = 1, per_page: int = 20) -> list[Account]:
        """
        Searches accounts by username or email with pagination.
        Case-insensitive substring match.

        Args:
            query: The search string to match against username or email.
            page: The page number (1-indexed). Defaults to 1.
            per_page: The number of items per page. Defaults to 20.

        Returns:
            list[Account]: A list of matching Account domain entities
                for the given page.
        """
        pass

    @abstractmethod
    def count_search(self, query: str) -> int:
        """
        Returns the total number of accounts matching the search query.

        Args:
            query: The search string to match against username or email.

        Returns:
            int: The total count of matching accounts.
        """
        pass

    @abstractmethod
    def delete(self, account_id: int) -> None:
        """
        Deletes an account by its unique identifier.

        The database will apply ON DELETE SET NULL for articles authored
        by this account and ON DELETE CASCADE for their comments.

        Args:
            account_id (int): The unique identifier of the account to delete.
        """
        pass
