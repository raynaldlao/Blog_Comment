from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


class CommentModel(SqlAlchemyModel):
    """
    SQLAlchemy ORM model for comments used in the new architecture.

    comment_reply_to uses ON DELETE SET NULL so that replies to a deleted
    comment become top-level comments instead of being cascaded away.
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
    comment_written_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.account_id", ondelete="SET NULL"),
        name="comment_written_account_id",
        type_=Integer,
        nullable=True,
    )
    comment_reply_to: Mapped[int | None] = mapped_column(
        ForeignKey("comments.comment_id", ondelete="SET NULL"),
        name="comment_reply_to",
        type_=Integer,
        nullable=True,
    )
    comment_content: Mapped[str] = mapped_column(
        name="comment_content", type_=String(5000), nullable=False
    )
    comment_posted_at: Mapped[datetime] = mapped_column(
        name="comment_posted_at", type_=TIMESTAMP, server_default=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(
        name="is_deleted", type_=Boolean, default=False, nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        name="deleted_at", type_=TIMESTAMP, nullable=True,
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        name="edited_at", type_=TIMESTAMP, nullable=True,
    )
