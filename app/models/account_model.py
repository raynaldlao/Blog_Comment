from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Column,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from database.database_setup import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint(sqltext="account_role IN ('admin', 'author', 'user')", name="accounts_role_check"),)

    account_id = Column(name="account_id", type_=Integer, primary_key=True, autoincrement=True)
    account_username = Column(name="account_username", type_=Text, unique=True, nullable=False)
    account_password = Column(name="account_password", type_=Text, nullable=False)
    account_email = Column(name="account_email", type_=Text)
    account_role = Column(name="account_role", type_=Text, nullable=False)
    account_created_at = Column(name="account_created_at", type_=TIMESTAMP, server_default=func.now())

    articles = relationship(argument="Article", back_populates="article_author", cascade="all, delete-orphan")
    comments = relationship(argument="Comment", back_populates="comment_author", cascade="all, delete-orphan")
