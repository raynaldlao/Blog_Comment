from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from database.database_setup import Base


class Article(Base):
    """
    Represents a blog article.

    Attributes:
        article_id (int): Unique identifier for the article.
        article_author_id (int): Foreign key to the author's account.
        article_title (str): Title of the article.
        article_content (str): Full text content of the article.
        article_published_at (datetime): Timestamp when the article was published.
        article_author (relationship): The Account instance of the author.
        article_comments (relationship): List of comments associated with this article.
    """
    __tablename__ = "articles"

    article_id = Column(name="article_id", type_=Integer, primary_key=True, autoincrement=True)
    article_author_id = Column(ForeignKey("accounts.account_id", ondelete="CASCADE"), name="article_author_id", type_=Integer, nullable=False)
    article_title = Column(name="article_title", type_=Text, nullable=False)
    article_content = Column(name="article_content", type_=Text, nullable=False)
    article_published_at = Column(name="article_published_at", type_=TIMESTAMP, server_default=func.now())

    article_author = relationship(argument="Account", back_populates="articles")
    article_comments = relationship(argument="Comment", back_populates="comment_article", cascade="all, delete-orphan")
