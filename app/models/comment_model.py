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
