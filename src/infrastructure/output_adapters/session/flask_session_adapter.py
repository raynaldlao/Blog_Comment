from flask import session as flask_session

from src.application.domain.account import Account
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository


class FlaskSessionAdapter(AccountSessionRepository):
    """
    Implementation of the AccountSessionRepository using Flask's internal cookies.
    Acts as an Output Adapter supporting AccountSessionRepository.
    """

    _KEY_USER_ID = "user_id"
    _KEY_USERNAME = "username"
    _KEY_ROLE = "role"

    def __init__(self, account_repository: AccountRepository):
        """
        Initializes the session adapter.

        Args:
            account_repository (AccountRepository): Repository to fetch the domain Account from its ID.
        """
        self.account_repository = account_repository

    def save_account(self, account: Account) -> None:
        """
        Stores the authenticated account in the current session.

        Args:
            account (Account): The domain entity to associate with the current session.
        """
        flask_session[self._KEY_USER_ID] = account.account_id
        flask_session[self._KEY_USERNAME] = account.account_username
        flask_session[self._KEY_ROLE] = account.account_role.value

    def get_account(self) -> Account | None:
        """
        Retrieves the currently connected domain Account.

        Returns:
            Account | None: The domain account if a session is active, otherwise None.
        """
        account_id = flask_session.get(self._KEY_USER_ID)

        if not account_id or not str(account_id).isdigit():
            return None

        return self.account_repository.get_by_id(int(str(account_id)))

    def clear(self) -> None:
        """
        Wipes the current session data, logging the user out.
        """
        flask_session.clear()
