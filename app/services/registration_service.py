from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session

from app.models.account_model import Account


class RegistrationService:
    """
    Service class responsible for handling user registration and account creation logic.
    """

    def __init__(self, session: Session | scoped_session[Session]):
        """
        Initialize the service with a database session (Dependency Injection).

        Args:
            session (Session | scoped_session[Session]): The SQLAlchemy database session to use for queries.
        """
        self.session = session

    def create_account(self, username: str, password: str) -> Account | None:
        """
        Creates a new user account with the default 'user' role if the username is not already taken.

        Args:
            username (str): The username for the new account.
            password (str): The plaintext password for the new account.

        Returns:
            Account | None: The newly created Account instance, or None if the username already exists.
        """
        existing_user_query = select(Account).where(Account.account_username == username)
        existing_user = self.session.execute(existing_user_query).scalar_one_or_none()

        if existing_user:
            return None

        new_account = Account(account_username=username, account_password=password, account_role="user")
        self.session.add(new_account)
        self.session.commit()
        return new_account
