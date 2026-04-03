from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


class ArticleModel(SqlAlchemyModel):
    """
    SQLAlchemy ORM model for the 'articles' table.
    """

    __tablename__ = "articles"

    article_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_author_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    article_title: Mapped[str] = mapped_column(Text, nullable=False)
    article_content: Mapped[str] = mapped_column(Text, nullable=False)
    article_published_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
