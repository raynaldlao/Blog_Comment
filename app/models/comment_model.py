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


class Comment(Base):
    """
    Represents a comment or a reply on an article.

    Attributes:
        comment_id (int): Unique identifier for the comment (Primary Key).
        comment_article_id (int): Foreign key referencing the associated article.
        comment_written_account_id (int): Foreign key referencing the author's account.
        comment_reply_to (int | None): Foreign key referencing a parent comment (for replies).
        comment_content (str): Text content of the comment.
        comment_posted_at (datetime): Automated timestamp of when the comment was posted.
        comment_article (Article): Relationship to the parent article instance.
        comment_author (Account): Relationship to the author's account instance.
        reply_to_comment (Comment | None): Relationship to the parent comment if this is a reply.
        comment_replies (list[Comment]): Collection of replies (child comments).
    """

    __tablename__ = "comments"

    comment_id: Mapped[int] = mapped_column("comment_id", Integer, primary_key=True, autoincrement=True)
    comment_article_id: Mapped[int] = mapped_column(ForeignKey("articles.article_id", ondelete="CASCADE"), name="comment_article_id", nullable=False)
    comment_written_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.account_id", ondelete="CASCADE"), name="comment_written_account_id", nullable=False)
    comment_reply_to: Mapped[int | None] = mapped_column(ForeignKey("comments.comment_id"), name="comment_reply_to", nullable=True)
    comment_content: Mapped[str] = mapped_column("comment_content", Text, nullable=False)
    comment_posted_at: Mapped[datetime] = mapped_column("comment_posted_at", TIMESTAMP, server_default=func.now())

    comment_article = relationship("Article", back_populates="article_comments")
    comment_author = relationship("Account", back_populates="comments")

    reply_to_comment = relationship(
        "Comment",
        remote_side=[comment_id],
        back_populates="comment_replies",
        uselist=False,
    )
    comment_replies = relationship(
        "Comment",
        back_populates="reply_to_comment",
        cascade="all, delete-orphan",
    )
