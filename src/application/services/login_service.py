from src.application.domain.account import Account
from src.application.input_ports.account_session_management import AccountSessionManagementPort
from src.application.input_ports.login_management import LoginManagementPort
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.output_ports.password_hasher_repository import PasswordHasherRepository


class LoginService(LoginManagementPort, AccountSessionManagementPort):
    """
    Service responsible for handling user authentication and session lifecycle.
    Implements both LoginManagementPort (for authentication) and
    AccountSessionManagementPort (for reading/terminating sessions).
    """

    def __init__(
        self,
        account_repository: AccountRepository,
        session_repository: AccountSessionRepository,
        password_hasher_repository: PasswordHasherRepository,
    ):
        """
        Initializes the service with account repository, session management,
        and password hashing.

        Args:
            account_repository (AccountRepository): The repository for account data access.
            session_repository (AccountSessionRepository): The output port for session persistence.
            password_hasher_repository (PasswordHasherRepository): The port for password verification operations.
        """
        self.account_repository = account_repository
        self.session_repository = session_repository
        self.password_hasher_repository = password_hasher_repository

    def authenticate_user(self, username: str, password: str) -> Account | str:
        """
        Authenticates a user by verifying credentials.

        If successful, the account is saved in the session.
        If the existing password hash uses outdated parameters,
        it is seamlessly upgraded to the current Argon2 settings.

        Args:
            username (str): The username provided by the user.
            password (str): The plaintext password provided by the user.

        Returns:
            Account | str: The authenticated Account instance if
            credentials match, or an error message string if it fails.
        """

        account = self.account_repository.find_by_username(username)
        if not account:
            return "Invalid username or password."

        if self.password_hasher_repository.verify(password, account.account_password):
            if self.password_hasher_repository.check_needs_rehash(account.account_password):
                new_hash = self.password_hasher_repository.hash(password)
                account.account_password = new_hash
                self.account_repository.save(account)

            self.session_repository.save_account(account)
            return account

        return "Invalid username or password."

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

