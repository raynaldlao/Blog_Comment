from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session

from app.models.account_model import Account


class LoginService:
    """
    Service class responsible for handling user authentication logic.
    """

    def __init__(self, session: Session | scoped_session[Session]):
        """
        Initialize the service with a database session (Dependency Injection).
        Supports both standard Session and scoped_session proxy objects.

        Args:
            session (Session | scoped_session[Session]): The SQLAlchemy database session to use for queries.
        """
        self.session = session

    def authenticate_user(self, username: str, password: str) -> Account | None:
        """
        Validates the user's credentials against the database.

        Args:
            username (str): The username provided by the user.
            password (str): The plaintext password provided by the user.

        Returns:
            Account | None: The authenticated Account instance if credentials match, None otherwise.
        """
        query = select(Account).where(Account.account_username == username)
        user = self.session.execute(query).scalar_one_or_none()

        if user and user.account_password == password:
             return user

        return None
