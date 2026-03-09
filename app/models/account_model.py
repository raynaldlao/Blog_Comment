from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import Role
from database.database_setup import Base


class Account(Base):
    """
    Represents a user account in the system.

    Attributes:
        account_id (int): Unique identifier for the account (Primary Key).
        account_username (str): Unique username used for authentication.
        account_password (str): Securely hashed password string.
        account_email (str): Unique and mandatory email address for the user.
        account_role (str): Permissions role ('admin', 'author', or 'user').
        account_created_at (datetime): Automated timestamp of account creation.
        articles (list[Article]): Collection of articles authored by this account.
        comments (list[Comment]): Collection of comments written by this account.
    """

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint(
            sqltext=f"account_role IN ({', '.join([f"'{r.value}'" for r in Role])})",
            name="accounts_role_check",
        ),
    )

    account_id: Mapped[int] = mapped_column(
        name="account_id", type_=Integer, primary_key=True, autoincrement=True
    )
    account_username: Mapped[str] = mapped_column(
        name="account_username", type_=Text, unique=True, nullable=False
    )
    account_password: Mapped[str] = mapped_column(
        name="account_password", type_=Text, nullable=False
    )
    account_email: Mapped[str] = mapped_column(
        name="account_email", type_=Text, unique=True, nullable=False
    )
    account_role: Mapped[str] = mapped_column(
        name="account_role", type_=Text, nullable=False
    )
    account_created_at: Mapped[datetime] = mapped_column(
        name="account_created_at", type_=TIMESTAMP, server_default=func.now()
    )

    articles = relationship(
        argument="Article",
        back_populates="article_author",
        cascade="all, delete-orphan",
    )
    comments = relationship(
        argument="Comment",
        back_populates="comment_author",
        cascade="all, delete-orphan",
    )
