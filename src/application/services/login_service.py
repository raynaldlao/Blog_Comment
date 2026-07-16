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

    def get_account_by_username(self, username: str) -> Account | None:
        """
        Retrieves a domain Account by its unique username via the repository.

        Args:
            username: The username to look up.

        Returns:
            Account | None: The domain Account if found, None otherwise.
        """
        return self.account_repository.find_by_username(username)

    def update_avatar(self, avatar_file_id: str | None) -> None:
        """
        Sets or clears the avatar_file_id for the currently authenticated account.

        Retrieves the current account from the session and delegates
        the persistence update to the account repository.

        Pass None to remove the avatar reference.

        Args:
            avatar_file_id: The UUID of the uploaded avatar file, or None to clear.
        """
        account = self.get_current_account()
        if account is None:
            return
        self.account_repository.update_avatar(account.account_id, avatar_file_id)

    def update_email(self, new_email: str) -> str | None:
        """
        Updates the email address for the currently logged-in account.

        Retrieves the current account from the session, checks that the new
        email is not already used by a different account, and persists the
        change via the account repository.

        Args:
            new_email: The new email address to set.

        Returns:
            str | None: None on success, or an error message string if
                the email is already taken or the user is unauthenticated.
        """
        account = self.get_current_account()
        if not account:
            return "You must be signed in to update your email."

        if new_email == account.account_email:
            return None

        existing = self.account_repository.find_by_email(new_email)
        if existing and existing.account_id != account.account_id:
            return "This email is already taken."

        self.account_repository.update_email(account.account_id, new_email)
        return None

    def get_all_accounts(self) -> list[Account]:
        """
        Retrieves all accounts via the account repository.

        Returns:
            list[Account]: A list of all Account domain entities.
        """
        return self.account_repository.get_all()
