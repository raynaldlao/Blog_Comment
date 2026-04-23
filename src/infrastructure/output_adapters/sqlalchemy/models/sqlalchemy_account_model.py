from datetime import datetime

from sqlalchemy import TIMESTAMP, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


class AccountModel(SqlAlchemyModel):
    """
    SQLAlchemy ORM model for the 'accounts' table.

    This class defines the database schema for user profiles, including
    authentication credentials, contact information, and roles.
    """

    __tablename__ = "accounts"

    account_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    account_password: Mapped[str] = mapped_column(Text, nullable=False)
    account_email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    account_role: Mapped[str] = mapped_column(Text, nullable=False)
    account_created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
