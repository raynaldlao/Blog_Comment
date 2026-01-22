from sqlalchemy import TIMESTAMP, CheckConstraint, Column, ForeignKey, Integer, Text, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("account_role IN ('admin', 'author', 'user')", name="accounts_role_check"),
    )

    account_id = Column("account_id", Integer, primary_key=True, autoincrement=True)
    account_username = Column("account_username", Text, unique=True, nullable=False)
    account_password = Column("account_password", Text, nullable=False)
    account_email = Column("account_email", Text)
    account_role = Column("account_role", Text, nullable=False)
    account_created_at = Column("account_created_at", TIMESTAMP, server_default=func.now())

    articles = relationship("Article", back_populates="article_author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="comment_author", cascade="all, delete-orphan")


class Article(Base):
    __tablename__ = "articles"

    article_id = Column("article_id", Integer, primary_key=True, autoincrement=True)
    article_author_id = Column("article_author_id", Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    article_title = Column("article_title", Text, nullable=False)
    article_content = Column("article_content", Text, nullable=False)
    article_published_at = Column("article_published_at", TIMESTAMP, server_default=func.now())

    article_author = relationship("Account", back_populates="articles")
    article_comments = relationship("Comment", back_populates="comment_article", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column("comment_id", Integer, primary_key=True, autoincrement=True)
    comment_article_id = Column("comment_article_id", Integer, ForeignKey("articles.article_id", ondelete="CASCADE"), nullable=False)
    comment_written_account_id = Column("comment_written_account_id", Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    comment_reply_to = Column("comment_reply_to", Integer, ForeignKey("comments.comment_id"), nullable=True)
    comment_content = Column("comment_content", Text, nullable=False)
    comment_posted_at = Column("comment_posted_at", TIMESTAMP, server_default=func.now())

    comment_article = relationship("Article", back_populates="article_comments")
    comment_author = relationship("Account", back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[comment_id])
