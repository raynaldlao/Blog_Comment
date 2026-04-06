from src.application.domain.account import Account, AccountRole
from src.application.input_ports.registration_management import RegistrationManagementPort
from src.application.output_ports.account_repository import AccountRepository


class RegistrationService(RegistrationManagementPort):
    """
    Service responsible for handling user registration.
    Implements the RegistrationManagementPort.
    """

    def __init__(self, account_repository: AccountRepository):
        """
        Initialize the service with an AccountRepository (Dependency Injection).

        Args:
            account_repository (AccountRepository): The repository port
            for account data access.
        """
        self.account_repository = account_repository

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
