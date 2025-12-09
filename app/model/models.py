from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, unique=True, nullable=False)
    email = Column(Text)
    role = Column(Text, nullable=False)  
    created_at = Column(TIMESTAMP)

    articles = relationship("Article", back_populates="writer", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="commenter", cascade="all, delete-orphan")


class Article(Base):
    __tablename__ = "articles"

    article_id = Column(Integer, primary_key=True, autoincrement=True)
    writer_id = Column(Integer, ForeignKey("accounts.account_id"), nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    published_at = Column(TIMESTAMP)

    writer = relationship("Account", back_populates="articles")
    feedbacks = relationship("Feedback", back_populates="article", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    article_ref = Column(Integer, ForeignKey("articles.article_id"), nullable=False)
    commenter_id = Column(Integer, ForeignKey("accounts.account_id"), nullable=False)
    reply_to = Column(Integer, ForeignKey("feedback.feedback_id"))
    message = Column(Text, nullable=False)
    posted_at = Column(TIMESTAMP)

    article = relationship("Article", back_populates="feedbacks")
    commenter = relationship("Account", back_populates="feedbacks")
    replies = relationship("Feedback", remote_side=[feedback_id])
