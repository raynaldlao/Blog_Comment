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
    __tablename__ = "articles"

    article_id = Column(name="article_id", type_=Integer, primary_key=True, autoincrement=True)
    article_author_id = Column(ForeignKey("accounts.account_id", ondelete="CASCADE"), name="article_author_id", type_=Integer, nullable=False)
    article_title = Column(name="article_title", type_=Text, nullable=False)
    article_content = Column(name="article_content", type_=Text, nullable=False)
    article_published_at = Column(name="article_published_at", type_=TIMESTAMP, server_default=func.now())

    article_author = relationship(argument="Account", back_populates="articles")
    article_comments = relationship(argument="Comment", back_populates="comment_article", cascade="all, delete-orphan")
