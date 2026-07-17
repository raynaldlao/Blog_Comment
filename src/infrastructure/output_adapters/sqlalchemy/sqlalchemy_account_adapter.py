from typing import cast

from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.application.application_exceptions import AccountAlreadyExistsError
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

    def get_by_ids(self, account_ids: list[int]) -> list[Account]:
        """
        Retrieves a list of accounts by their unique IDs in a single batch.

        Args:
            account_ids (list[int]): A list of account identifiers.

        Returns:
            list[Account]: A list of found Account domain entities.
        """
        if not account_ids:
            return []

        models = (
            self._session.query(AccountModel)
            .filter(AccountModel.account_id.in_(account_ids))
            .all()
        )
        return [self._to_domain(model) for model in models]

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
        Saves a domain account entity to the database.

        If the account has an existing positive ID, updates the corresponding
        record; otherwise creates a new one. The account ID is updated in place
        after insertion.

        Args:
            account (Account): The domain entity to save.

        Raises:
            AccountAlreadyExistsError: If a unique constraint violation occurs
                on the username or email column.
            RuntimeError: If an unexpected unique constraint violation occurs.
        """
        if account.account_id and account.account_id > 0:
            model = self._session.get(AccountModel, account.account_id)
            if not model:
                model = AccountModel()
        else:
            model = AccountModel()

        model.account_username = account.account_username
        model.account_password = account.account_password
        model.account_email = account.account_email
        model.account_role = account.account_role.value
        self._session.add(model)
        try:
            self._session.commit()
        except IntegrityError as e:
            self._session.rollback()
            constraint_name = cast(UniqueViolation, e.orig).diag.constraint_name if e.orig else None

            if constraint_name == "accounts_account_username_key":
                raise AccountAlreadyExistsError(
                    "This username is already taken."
                ) from None
            elif constraint_name == "accounts_account_email_key":
                raise AccountAlreadyExistsError(
                    "This email is already taken."
                ) from None
            else:
                raise RuntimeError(
                    f"Unexpected unique constraint violation: {constraint_name}"
                ) from None
        account.account_id = model.account_id

    def update_avatar(self, account_id: int, avatar_file_id: str | None) -> None:
        """
        Updates the avatar_file_id for the given account directly in the database.

        Performs a targeted column update without loading or saving the full
        Account entity, keeping the responsibility focused and avoiding
        accidental overwrites of other fields.

        Args:
            account_id: The ID of the account to update.
            avatar_file_id: The new avatar file UUID, or None to remove.
        """
        model = self._session.get(AccountModel, account_id)
        if model is None:
            return
        model.avatar_file_id = avatar_file_id
        self._session.commit()

    def update_email(self, account_id: int, new_email: str) -> None:
        """
        Updates the email address for the given account directly in the database.

        Performs a targeted column update and commits the transaction.
        Catches unique constraint violations and re-raises as a domain exception.

        Args:
            account_id: The ID of the account to update.
            new_email: The new email address to set.

        Raises:
            AccountAlreadyExistsError: If the new email is already taken
                by another account.
        """
        model = self._session.get(AccountModel, account_id)
        if model is None:
            return
        model.account_email = new_email
        try:
            self._session.commit()
        except IntegrityError as e:
            self._session.rollback()
            constraint_name = cast(UniqueViolation, e.orig).diag.constraint_name if e.orig else None
            if constraint_name == "accounts_account_email_key":
                raise AccountAlreadyExistsError("This email is already taken.") from None
            raise

    def update_password(self, account_id: int, new_hashed_password: str) -> None:
        """
        Updates the password hash for the given account directly in the database.

        Performs a targeted column update and commits the transaction.

        Args:
            account_id: The ID of the account to update.
            new_hashed_password: The new Argon2 hash to store.
        """
        model = self._session.get(AccountModel, account_id)
        if model is None:
            return
        model.account_password = new_hashed_password
        self._session.commit()

    def update_role(self, account_id: int, new_role: str) -> None:
        """
        Updates the role for the given account directly in the database.

        Args:
            account_id: The ID of the account to update.
            new_role: The new role string ("user" or "author").
        """
        model = self._session.get(AccountModel, account_id)
        if model is None:
            return
        model.account_role = new_role
        self._session.commit()

    def get_all(self) -> list[Account]:
        """
        Retrieves all accounts from the database.

        Returns:
            list[Account]: A list of all Account domain entities.
        """
        models = self._session.query(AccountModel).all()
        return [self._to_domain(model) for model in models]

    def delete(self, account_id: int) -> None:
        """
        Deletes an account by its unique identifier.

        The database will apply ON DELETE SET NULL for articles authored
        by this account and ON DELETE CASCADE for their comments.

        Args:
            account_id (int): The unique identifier of the account to delete.

        Raises:
            ValueError: If no account with the given ID exists.
        """
        model = self._session.get(AccountModel, account_id)
        if model is None:
            raise ValueError(f"Account with id {account_id} not found.")
        self._session.delete(model)
        self._session.commit()
