from datetime import datetime

from src.application.domain.account import Account, AccountRole
from src.application.output_ports.account_repository import AccountRepository


class InMemoryAccountRepository(AccountRepository):
    """
    In-memory implementation of the AccountRepository.
    Uses a dictionary to store accounts, designed for unit testing.
    """

    def __init__(self):
        """
        Initializes the repository with an empty internal dictionary and ID counter.
        """
        self._accounts: dict[int, Account] = {}
        self._next_id = 1

    def save(self, account: Account) -> None:
        """
        Saves a new account or updates an existing one. Assigns a new ID if 0.

        Args:
            account (Account): The Account domain entity to save.
        """
        if account.account_id == 0:
            account.account_id = self._next_id
            self._next_id += 1
        self._accounts[account.account_id] = account

    def get_by_id(self, account_id: int) -> Account | None:
        """
        Retrieves an account by its unique ID.

        Args:
            account_id (int): ID to look for.

        Returns:
            Account | None: The domain Account or None.
        """
        return self._accounts.get(account_id)

    def get_by_ids(self, account_ids: list[int]) -> list[Account]:
        """
        Retrieves multiple accounts by their IDs.

        Args:
            account_ids (list[int]): List of account IDs.

        Returns:
            list[Account]: A list of found Account entities.
        """
        return [acc for acc in self._accounts.values() if acc.account_id in account_ids]

    def find_by_username(self, username: str) -> Account | None:
        """
        Searches for an account matching the given username.

        Args:
            username (str): The username to search for.

        Returns:
            Account | None: The domain Account or None if not matching.
        """
        for account in self._accounts.values():
            if account.account_username == username:
                return account
        return None

    def find_by_email(self, email: str) -> Account | None:
        """
        Searches for an account matching the given email.

        Args:
            email (str): The email to search for.

        Returns:
            Account | None: The domain Account or None.
        """
        for account in self._accounts.values():
            if account.account_email == email:
                return account
        return None

    def update_avatar(self, account_id: int, avatar_file_id: str | None) -> None:
        """
        Updates the avatar_file_id for the given account in memory.

        Args:
            account_id: The ID of the account to update.
            avatar_file_id: The new avatar file UUID, or None to remove.
        """
        account = self._accounts.get(account_id)
        if account is None:
            return
        account.avatar_file_id = avatar_file_id

    def update_email(self, account_id: int, new_email: str) -> None:
        """
        Updates the email address for the given account in memory.

        Args:
            account_id: The ID of the account to update.
            new_email: The new email address to set.
        """
        account = self._accounts.get(account_id)
        if account is None:
            return
        account.account_email = new_email

    def update_password(self, account_id: int, new_hashed_password: str) -> None:
        """
        Updates the password hash for the given account in memory.

        Args:
            account_id: The ID of the account to update.
            new_hashed_password: The new password hash to store.
        """
        account = self._accounts.get(account_id)
        if account is None:
            return
        account.account_password = new_hashed_password

    def update_role(self, account_id: int, new_role: str) -> None:
        """
        Updates the account_role for the given account in memory.

        Args:
            account_id: The ID of the account to update.
            new_role: The new role string ("user" or "author").
        """
        account = self._accounts.get(account_id)
        if account is None:
            return
        account.account_role = AccountRole(new_role)

    def get_all(self) -> list[Account]:
        """
        Retrieves all accounts from the in-memory store.

        Returns:
            list[Account]: A list of all Account domain entities.
        """
        return list(self._accounts.values())

    def get_all_paginated(self, page: int = 1, per_page: int = 20) -> list[Account]:
        """
        Retrieves a paginated list of accounts, ordered by creation date desc.

        Args:
            page: The page number (1-indexed). Defaults to 1.
            per_page: The number of items per page. Defaults to 20.

        Returns:
            list[Account]: A list of Account domain entities for the given page.
        """
        sorted_accounts = sorted(
            self._accounts.values(),
            key=lambda a: a.account_created_at or datetime.min,
            reverse=True,
        )
        start = (page - 1) * per_page
        return sorted_accounts[start:start + per_page]

    def count_all(self) -> int:
        """
        Returns the total number of accounts in the in-memory store.

        Returns:
            int: The total count of accounts.
        """
        return len(self._accounts)

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
        q = query.lower()
        matched = [
            a for a in self._accounts.values()
            if q in a.account_username.lower() or q in a.account_email.lower()
        ]
        sorted_matched = sorted(
            matched,
            key=lambda a: a.account_created_at or datetime.min,
            reverse=True,
        )
        start = (page - 1) * per_page
        return sorted_matched[start:start + per_page]

    def count_search(self, query: str) -> int:
        """
        Returns the total number of accounts matching the search query.

        Args:
            query: The search string to match against username or email.

        Returns:
            int: The total count of matching accounts.
        """
        q = query.lower()
        return sum(
            1 for a in self._accounts.values()
            if q in a.account_username.lower() or q in a.account_email.lower()
        )

    def update_ban_status(self, account_id: int, is_banned: bool, ban_reason: str | None) -> None:
        """
        Sets or clears the ban status for the given account in memory.

        Args:
            account_id: The ID of the account to update.
            is_banned: True to ban, False to unban.
            ban_reason: Optional reason for the ban, or None to clear.

        Raises:
            ValueError: If no account with the given ID exists.
        """
        account = self._accounts.get(account_id)
        if account is None:
            raise ValueError(f"Account with id {account_id} not found.")
        account.is_banned = is_banned
        account.ban_reason = ban_reason

    def delete(self, account_id: int) -> None:
        """
        Deletes an account by its unique identifier from the in-memory store.

        Args:
            account_id (int): The unique identifier of the account to delete.
        """
        self._accounts.pop(account_id, None)
