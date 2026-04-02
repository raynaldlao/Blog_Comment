from sqlalchemy.orm import Session

from src.application.domain.account import Account
from src.application.output_ports.account_repository import AccountRepository
from src.infrastructure.output_adapters.dto.account_record import AccountRecord
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel


class SqlAlchemyAccountAdapter(AccountRepository):
    """
    SQLAlchemy-based implementation of the AccountRepository port.

    This adapter manages the persistence and retrieval of Account domain entities
    using SQLAlchemy ORM and the PostgreSQL database.
    """

    def __init__(self, session: Session):
        """
        Initializes the adapter with a SQLAlchemy session.

        Args:
            session (Session): An active SQLAlchemy database session.
        """
        self._session = session

    def _to_domain(self, model: AccountModel) -> Account:
        """
        Maps a SQLAlchemy ORM model to a Domain Entity via a DTO.

        Args:
            model (AccountModel): The database record to convert.

        Returns:
            Account: The converted Domain Entity.
        """
        record = AccountRecord.model_validate(model)
        return record.to_domain()

    def find_by_username(self, username: str) -> Account | None:
        """
        Retrieves a domain account by its unique username.

        Args:
            username (str): The username to search for.

        Returns:
            Account | None: The domain account if found, otherwise None.
        """
        model = self._session.query(AccountModel).filter_by(account_username=username).first()
        if model is None:
            return None
        return self._to_domain(model)

    def get_by_id(self, account_id: int) -> Account | None:
        """
        Retrieves a domain account by its primary key.

        Args:
            account_id (int): The unique identifier of the account.

        Returns:
            Account | None: The domain account if found, otherwise None.
        """
        model = self._session.get(AccountModel, account_id)
        if model is None:
            return None
        return self._to_domain(model)

    def find_by_email(self, email: str) -> Account | None:
        """
        Retrieves a domain account by its unique email address.

        Args:
            email (str): The email address to search for.

        Returns:
            Account | None: The domain account if found, otherwise None.
        """
        model = self._session.query(AccountModel).filter_by(account_email=email).first()
        if model is None:
            return None
        return self._to_domain(model)

    def save(self, account: Account) -> None:
        """
        Persists a domain account entity into the database.

        Args:
            account (Account): The domain entity to save.
        """
        model = AccountModel()
        model.account_username = account.account_username
        model.account_password = account.account_password
        model.account_email = account.account_email
        model.account_role = account.account_role.value
        self._session.add(model)
        self._session.commit()
