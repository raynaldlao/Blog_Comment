from src.application.domain.account import Account
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
