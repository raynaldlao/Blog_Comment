from src.application.domain.account import Account
from src.application.input_ports.account_session_management import AccountSessionManagement
from src.application.input_ports.login_management import LoginManagementPort
from src.application.output_ports.account_repository import AccountRepository


class LoginService(LoginManagementPort):
    """
    Service responsible for handling user authentication.
    Implements the LoginManagementPort.
    """

    def __init__(
        self,
        account_repository: AccountRepository,
        session_service: AccountSessionManagement
    ):
        """
        Initializes the service with both account repository and session management.

        Args:
            account_repository (AccountRepository): The repository for account data access.
            session_service (AccountSessionManagement): The service for session state coordination.
        """
        self.account_repository = account_repository
        self.session_service = session_service

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
            self.session_service.start_session(account)
            return account

        # TODO: Raise InvalidCredentialsException
        return None
