from src.application.domain.account import Account, AccountSessionKey
from src.application.input_ports.account_session_management import AccountSessionManagement
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository


class AccountSessionService(AccountSessionManagement):
    """
    Service providing session-related business logic.
    """

    def __init__(
        self,
        session_repository: AccountSessionRepository,
        account_repository: AccountRepository
    ):
        """
        Initializes the service with both session storage and account data access.

        Args:
            session_repository (AccountSessionRepository): The storage-level port.
            account_repository (AccountRepository): The repository for retrieving account entities.
        """
        self._session_repository = session_repository
        self._account_repository = account_repository

    def start_session(self, account: Account) -> None:
        """
        Populates the session storage with identification data extracted from the account.

        Args:
            account (Account): The domain entity being logged in.
        """
        self._session_repository.store_value(AccountSessionKey.USER_ID, account.account_id)
        self._session_repository.store_value(AccountSessionKey.USERNAME, account.account_username)
        self._session_repository.store_value(AccountSessionKey.ROLE, account.account_role.value)

    def get_current_account(self) -> Account | None:
        """
        Reconstructs the full domain Account for the presently active session.

        Returns:
            Account | None: The domain entity if its ID is found in session, otherwise None.
        """
        account_id = self._session_repository.retrieve_value(AccountSessionKey.USER_ID)
        if not account_id:
            return None

        return self._account_repository.get_by_id(int(account_id))

    def terminate_session(self) -> None:
        """
        Wipes the identification data from the session storage, effectively logging out.
        """
        self._session_repository.invalidate()
