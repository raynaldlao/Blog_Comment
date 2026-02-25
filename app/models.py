from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Column,
    ForeignKey,
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


class Article(Base):
    __tablename__ = "articles"

    article_id = Column(name="article_id", type_=Integer, primary_key=True, autoincrement=True)
    article_author_id = Column(ForeignKey("accounts.account_id", ondelete="CASCADE"), name="article_author_id", type_=Integer, nullable=False)
    article_title = Column(name="article_title", type_=Text, nullable=False)
    article_content = Column(name="article_content", type_=Text, nullable=False)
    article_published_at = Column(name="article_published_at", type_=TIMESTAMP, server_default=func.now())

    article_author = relationship(argument="Account", back_populates="articles")
    article_comments = relationship(argument="Comment", back_populates="comment_article", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(name="comment_id", type_=Integer, primary_key=True, autoincrement=True)
    comment_article_id = Column(ForeignKey("articles.article_id", ondelete="CASCADE"), name="comment_article_id", type_=Integer, nullable=False)
    comment_written_account_id = Column(ForeignKey("accounts.account_id", ondelete="CASCADE"), name="comment_written_account_id", type_=Integer, nullable=False)
    comment_reply_to = Column(ForeignKey("comments.comment_id"), name="comment_reply_to", type_=Integer, nullable=True)
    comment_content = Column(name="comment_content", type_=Text, nullable=False)
    comment_posted_at = Column(name="comment_posted_at", type_=TIMESTAMP, server_default=func.now())

    comment_article = relationship(argument="Article", back_populates="article_comments")
    comment_author = relationship(argument="Account", back_populates="comments")
    reply_to_comment = relationship(
        argument="Comment",
        remote_side=[comment_id],
        back_populates="comment_replies",
        uselist=False,
    )
    comment_replies = relationship(
        argument="Comment",
        back_populates="reply_to_comment",
        cascade="all, delete-orphan",
    )
