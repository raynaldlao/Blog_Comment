from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


class CommentModel(SqlAlchemyModel):
    """
    SQLAlchemy ORM model for comments used in the new architecture.
    """

    __tablename__ = "comments"
    __table_args__ = {"extend_existing": True}

    comment_id: Mapped[int] = mapped_column(
        name="comment_id", type_=Integer, primary_key=True, autoincrement=True
    )
    comment_article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.article_id", ondelete="CASCADE"),
        name="comment_article_id",
        type_=Integer,
        nullable=False,
    )
    comment_written_account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        name="comment_written_account_id",
        type_=Integer,
        nullable=False,
    )
    comment_reply_to: Mapped[int | None] = mapped_column(
        ForeignKey("comments.comment_id"),
        name="comment_reply_to",
        type_=Integer,
        nullable=True,
    )
    comment_content: Mapped[str] = mapped_column(
        name="comment_content", type_=Text, nullable=False
    )
    comment_posted_at: Mapped[datetime] = mapped_column(
        name="comment_posted_at", type_=TIMESTAMP, server_default=func.now()
    )
