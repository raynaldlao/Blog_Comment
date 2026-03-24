from src.application.domain.account import Account
from src.application.output_ports.account_repository import AccountRepository


class LoginService:
    """
    Use case responsible for handling user authentication logic.
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

        return None
