from abc import ABC, abstractmethod

from src.application.domain.account import Account


class AccountSessionManagementPort(ABC):
    """
    Input Port for managing the user's active session.
    Provides methods for the interface layer to retrieve identity and terminate sessions.
    """

    @abstractmethod
    def get_current_account(self) -> Account | None:
        """
        Retrieves the domain Account associated with the current session.

        Returns:
            Account | None: The domain representation of the connected user,
                            or None if unauthenticated.
        """
        pass

    @abstractmethod
    def terminate_session(self) -> None:
        """
        Terminates the current active session, effectively logging the user out.
        """
        pass
