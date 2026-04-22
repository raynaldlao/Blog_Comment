from src.application.domain.account import Account
from src.application.input_ports.account_session_management import AccountSessionManagementPort
from src.application.input_ports.login_management import LoginManagementPort
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository


class LoginService(LoginManagementPort, AccountSessionManagementPort):
    """
    Service responsible for handling user authentication and session lifecycle.
    Implements both LoginManagementPort (for authentication) and
    AccountSessionManagementPort (for reading/terminating sessions).
    """

    def __init__(
        self,
        account_repository: AccountRepository,
        session_repository: AccountSessionRepository
    ):
        """
        Initializes the service with both account repository and session management.

        Args:
            account_repository (AccountRepository): The repository for account data access.
            session_repository (AccountSessionRepository): The output port for session persistence.
        """
        self.account_repository = account_repository
        self.session_repository = session_repository

    def authenticate_user(self, username: str, password: str) -> Account | None:
        """
        Validates the user's credentials.

        Args:
            username (str): The username provided by the user.
            password (str): The plaintext password provided by the user.

        Returns:
            Account | None: The authenticated Account instance if
            credentials match, None otherwise.
        """

        account = self.account_repository.find_by_username(username)
        if account and account.account_password == password:
            self.session_repository.save_account(account)
            return account

        # TODO: Raise InvalidCredentialsException
        return None

    def get_current_account(self) -> Account | None:
        """
        Retrieves the domain Account associated with the current session.

        Returns:
            Account | None: The domain representation of the connected user,
                            or None if unauthenticated.
        """
        return self.session_repository.get_account()

    def terminate_session(self) -> None:
        """
        Terminates the current active session, effectively logging the user out.
        """
        self.session_repository.clear()

