from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database_setup import Base


class Article(Base):
    """
    Represents a blog article.

    Attributes:
        article_id (int): Unique identifier for the article (Primary Key).
        article_author_id (int): Foreign key referencing the author's Account.
        article_title (str): Title of the article.
        article_content (str): Full text content of the article.
        article_published_at (datetime): Automated timestamp of publication.
        article_author (Account): Relationship to the author's Account instance.
        article_comments (list[Comment]): Collection of comments
        linked to this article.
    """

    __tablename__ = "articles"

    article_id: Mapped[int] = mapped_column(
        name="article_id", type_=Integer, primary_key=True, autoincrement=True
    )
    article_author_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        name="article_author_id",
        type_=Integer,
        nullable=False,
    )
    article_title: Mapped[str] = mapped_column(
        name="article_title", type_=Text, nullable=False
    )
    article_content: Mapped[str] = mapped_column(
        name="article_content", type_=Text, nullable=False
    )
    article_published_at: Mapped[datetime] = mapped_column(
        name="article_published_at", type_=TIMESTAMP, server_default=func.now()
    )

    article_author = relationship(argument="Account", back_populates="articles")
    article_comments = relationship(
        argument="Comment",
        back_populates="comment_article",
        cascade="all, delete-orphan",
    )
