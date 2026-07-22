from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


class ArticleModel(SqlAlchemyModel):
    """
    SQLAlchemy ORM model for the 'articles' table.

    article_author_id uses ON DELETE SET NULL to preserve articles
    when the author account is deleted (author becomes "Anonymous").
    article_description is a VARCHAR(300) short summary displayed
    in the article list view.
    """

    __tablename__ = "articles"

    article_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_author_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.account_id", ondelete="SET NULL"),
        nullable=True,
    )
    article_title: Mapped[str] = mapped_column(Text, nullable=False)
    article_description: Mapped[str] = mapped_column(
        String(300), nullable=False, server_default="", default="",
    )
    article_content: Mapped[str] = mapped_column(Text, nullable=False)
    article_published_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    article_edited_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
