from src.application.domain.account import Account, AccountRole
from src.application.input_ports.account_management import AccountManagementPort
from src.application.output_ports.account_repository import AccountRepository


class AccountService(AccountManagementPort):
    """
    Service responsible for handling all account-related logic,
    including authentication and registration.
    Implements the AccountManagementPort.
    Depends on the AccountRepository output port for data access.
    """

    def __init__(self, account_repository: AccountRepository):
        """
        Initialize the service with an AccountRepository (Dependency Injection).

        Args:
            account_repository (AccountRepository): The repository port
            for account data access.
        """
        self.account_repository = account_repository

    def authenticate_user(self, username: str, password: str) -> Account | None:
        """
        Validates the user's credentials by retrieving the account
        from the repository and comparing the password.

        Args:
            username (str): The username provided by the user.
            password (str): The plaintext password provided by the user.

        Returns:
            Account | None: The authenticated Account instance if
            credentials match, None otherwise.
        """
        account = self.account_repository.find_by_username(username)

        if account and account.account_password == password:
            return account

        # TODO: Raise InvalidCredentialsException
        return None

    def create_account(self, username: str, password: str, email: str) -> Account | str:
        """
        Creates a new user account with the default 'user' role if the
        username and email are not already taken.

        Args:
            username (str): The username for the new account.
            password (str): The plaintext password for the new account.
            email (str): The email address for the new account.

        Returns:
            Account | str: The newly created Account domain entity, or an
            error message string if creation fails.
        """

        if self.account_repository.find_by_username(username):
            # TODO: Raise UsernameAlreadyTakenException
            return "This username is already taken."

        if self.account_repository.find_by_email(email):
            # TODO: Raise EmailAlreadyTakenException
            return "This email is already taken."

        new_account = Account(
            account_id=0,
            account_username=username,
            account_password=password,
            account_email=email,
            account_role=AccountRole.USER,
            account_created_at=None,
        )

        self.account_repository.save(new_account)
        return new_account
