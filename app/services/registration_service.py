from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session

from app.constants import Role
from app.models.account_model import Account


class RegistrationService:
    """
    Service class responsible for handling user registration and account creation logic.
    """

    def __init__(self, session: Session | scoped_session[Session]):
        """
        Initialize the service with a database session (Dependency Injection).

        Args:
            session (Session | scoped_session[Session]): The SQLAlchemy
            database session to use for queries.
        """
        self.session = session

    def create_account(self, username: str, password: str, email: str) -> Account | str:
        """
        Creates a new user account with the default 'user' role if the
        username and email are not already taken.

        Args:
            username (str): The username for the new account.
            password (str): The plaintext password for the new account.
            email (str): The email address for the new account.

        Returns:
            Account | str: The newly created Account instance, or an
            error message string if creation fails.
        """
        username_taken_message = "This username is already taken."
        email_taken_message = "This email is already taken."

        existing_username_query = select(Account).where(
            Account.account_username == username,
        )
        existing_username = self.session.execute(
            existing_username_query
        ).scalar_one_or_none()

        if existing_username:
            return username_taken_message

        existing_email_query = select(Account).where(Account.account_email == email)
        existing_email = self.session.execute(existing_email_query).scalar_one_or_none()

        if existing_email:
            return email_taken_message

        new_account = Account(
            account_username=username,
            account_password=password,
            account_email=email,
            account_role=Role.USER.value,
        )
        self.session.add(new_account)
        self.session.commit()
        return new_account
