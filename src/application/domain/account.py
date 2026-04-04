from datetime import datetime
from enum import Enum


class AccountRole(str, Enum):
    """
    Available roles for user accounts.
    Inheriting from str ensures JSON serializability and string comparisons work.
    """
    ADMIN = "admin"
    AUTHOR = "author"
    USER = "user"


class Account:
    """
    Represents a user account in the system.

    Attributes:
        account_id (int): Unique identifier for the account.
        account_username (str): Unique username used for authentication.
        account_password (str): Securely hashed password string.
        account_email (str): Unique email address for the user.
        account_role (AccountRole): Permissions role.
        account_created_at (datetime): Timestamp of account creation.
    """

    def __init__(
        self,
        account_id: int,
        account_username: str,
        account_password: str,
        account_email: str,
        account_role: AccountRole,
        account_created_at: datetime,
    ):
        """
        Initialize a user account.

        Args:
            account_id (int): Unique identifier for the account.
            account_username (str): Unique username used for authentication.
            account_password (str): Securely hashed password string.
            account_email (str): Unique email address for the user.
            account_role (AccountRole): Permissions role.
            account_created_at (datetime): Timestamp of account creation.
        """
        self.account_id = account_id
        self.account_username = account_username
        self.account_password = account_password
        self.account_email = account_email
        self.account_role = account_role
        self.account_created_at = account_created_at
