from abc import ABC, abstractmethod

from src.application.domain.account import Account


class AccountSessionManagement(ABC):
    """
    Interface for handling account session lifecycle.

    This port is used by the application to manage or verify the
    current user's presence without relying on a specific framework.
    """

    @abstractmethod
    def start_session(self, account: Account) -> None:
        """
        Starts a managed session for the given account.

        Args:
            account (Account): The domain entity to associate with the current session.
        """
        pass

    @abstractmethod
    def get_current_account(self) -> Account | None:
        """
        Retrieves the authenticated domain Account for the current session.

        Returns:
            Account | None: The domain account if a session is active, otherwise None.
        """
        pass

    @abstractmethod
    def terminate_session(self) -> None:
        """
        Clears the current session, logging the user out.
        """
        pass
