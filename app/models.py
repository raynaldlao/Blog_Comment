from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"

    account_id = Column("account_id", Integer, primary_key=True, autoincrement=True)
    username = Column("username", Text, unique=True, nullable=False)
    email = Column("email", Text)
    account_role = Column("account_role", Text, nullable=False)
    created_at = Column("created_at", TIMESTAMP)
    
    articles = relationship("Article", back_populates="writer", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="commenter", cascade="all, delete-orphan")


class Article(Base):
    __tablename__ = "articles"

    article_id = Column("article_id", Integer, primary_key=True, autoincrement=True)
    writer_id = Column("writer_id", Integer, ForeignKey("accounts.account_id"), nullable=False)
    title = Column("title", Text, nullable=False)
    content = Column("content", Text, nullable=False)
    published_at = Column("published_at", TIMESTAMP)

    writer = relationship("Account", back_populates="articles")
    feedbacks = relationship("Feedback", back_populates="article", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column("feedback_id", Integer, primary_key=True, autoincrement=True)
    article_ref = Column("article_ref", Integer, ForeignKey("articles.article_id"), nullable=False)
    commenter_id = Column("commenter_id", Integer, ForeignKey("accounts.account_id"), nullable=False)
    reply_to = Column("reply_to", Integer, ForeignKey("feedback.feedback_id"))
    message = Column("message", Text, nullable=False)
    posted_at = Column("posted_at", TIMESTAMP)

    article = relationship("Article", back_populates="feedbacks")
    commenter = relationship("Account", back_populates="feedbacks")
    replies = relationship("Feedback", remote_side=[feedback_id])
