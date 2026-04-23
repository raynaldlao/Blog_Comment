from abc import ABC, abstractmethod

from src.application.domain.account import Account


class AccountSessionRepository(ABC):
    """
    Interface for persistence and retrieval of the current user session.
    Acts as an Output Port, allowing the domain to mandate session state
    changes without knowing about HTTP or Cookies.
    """

    @abstractmethod
    def save_account(self, account: Account) -> None:
        """
        Stores the authenticated account in the current session.

        Args:
            account (Account): The domain entity to associate with the current session.
        """
        pass

    @abstractmethod
    def get_account(self) -> Account | None:
        """
        Retrieves the currently connected domain Account.

        Returns:
            Account | None: The domain account if a session is active, otherwise None.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Wipes the current session data, logging the user out.
        """
        pass
