from src.application.domain.account import Account
from src.application.output_ports.account_session_repository import AccountSessionRepository


class InMemoryAccountSessionRepository(AccountSessionRepository):
    """
    In-memory implementation of AccountSessionRepository, useful for testing
    authentication services without requiring a web framework context (like Flask).
    """

    def __init__(self):
        """
        Initializes an empty session state.
        """
        self._current_account: Account | None = None

    def save_account(self, account: Account) -> None:
        """
        Stores the authenticated account in the current session.

        Args:
            account (Account): The domain entity to associate with the current session.
        """
        self._current_account = account

    def get_account(self) -> Account | None:
        """
        Retrieves the currently connected domain Account.

        Returns:
            Account | None: The domain account if a session is active, otherwise None.
        """
        return self._current_account

    def clear(self) -> None:
        """
        Wipes the current session data, logging the user out.
        """
        self._current_account = None
