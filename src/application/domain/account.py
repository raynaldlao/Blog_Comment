from datetime import datetime


class Account:
    """
    Represents a user account in the system.

    Attributes:
        account_id (int): Unique identifier for the account.
        account_username (str): Unique username used for authentication.
        account_password (str): Securely hashed password string.
        account_email (str): Unique email address for the user.
        account_role (str): Permissions role ('admin', 'author', or 'user').
        account_created_at (datetime): Timestamp of account creation.
    """

    def __init__(
        self,
        account_id: int,
        account_username: str,
        account_password: str,
        account_email: str,
        account_role: str,
        account_created_at: datetime,
    ):
        self.account_id = account_id
        self.account_username = account_username
        self.account_password = account_password
        self.account_email = account_email
        self.account_role = account_role
        self.account_created_at = account_created_at
