from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Text,
    func,
    select,
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

    @classmethod
    def authenticate_username_password(cls, db_session, username, password):
        query = select(cls).where(cls.account_username == username)
        user = db_session.execute(query).scalar_one_or_none()

        if user and user.account_password == password:
            return user
        return None


class Article(Base):
    __tablename__ = "articles"

    article_id = Column(name="article_id", type_=Integer, primary_key=True, autoincrement=True)
    article_author_id = Column(
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        name="article_author_id",
        type_=Integer,
        nullable=False,
    )
    article_title = Column(name="article_title", type_=Text, nullable=False)
    article_content = Column(name="article_content", type_=Text, nullable=False)
    article_published_at = Column(name="article_published_at", type_=TIMESTAMP, server_default=func.now())

    article_author = relationship(argument="Account", back_populates="articles")
    article_comments = relationship(argument="Comment", back_populates="comment_article", cascade="all, delete-orphan")

    @classmethod
    def get_all_ordered_by_date(cls, db_session):
        query = select(cls).order_by(cls.article_published_at.desc())
        return db_session.execute(query).scalars().all()

    @classmethod
    def get_by_id(cls, db_session, article_id):
        return db_session.get(cls, article_id)

    @classmethod
    def create_article(cls, db_session, title, content, author_id):
        new_article = cls(article_title=title, article_content=content, article_author_id=author_id)
        db_session.add(new_article)
        db_session.commit()
        return new_article

    def update_article(self, db_session, title, content):
        self.article_title = title
        self.article_content = content
        db_session.commit()

    def delete_article(self, db_session):
        db_session.delete(self)
        db_session.commit()

    def is_editable_by(self, user_id, role):
        return role == "admin" or self.article_author_id == user_id


class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(name="comment_id", type_=Integer, primary_key=True, autoincrement=True)
    comment_article_id = Column(
        ForeignKey("articles.article_id", ondelete="CASCADE"),
        name="comment_article_id",
        type_=Integer,
        nullable=False,
    )
    comment_written_account_id = Column(
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        name="comment_written_account_id",
        type_=Integer,
        nullable=False,
    )
    comment_reply_to = Column(
        ForeignKey("comments.comment_id"),
        name="comment_reply_to",
        type_=Integer,
        nullable=True,
    )
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

    @classmethod
    def create_comment(cls, db_session, article_id, user_id, content):
        new_comment = cls(comment_article_id=article_id, comment_written_account_id=user_id, comment_content=content, comment_reply_to=None)
        db_session.add(new_comment)
        db_session.commit()
        return new_comment

    @classmethod
    def create_reply(cls, db_session, parent_comment_id, user_id, content):
        parent = db_session.get(cls, parent_comment_id)
        if not parent:
            return None

        new_reply = cls(comment_article_id=parent.comment_article_id, comment_written_account_id=user_id, comment_content=content, comment_reply_to=parent_comment_id)
        db_session.add(new_reply)
        db_session.commit()
        return new_reply

    @classmethod
    def get_by_id(cls, db_session, comment_id):
        return db_session.get(cls, comment_id)

    def delete_comment(self, db_session):
        db_session.delete(self)
        db_session.commit()
