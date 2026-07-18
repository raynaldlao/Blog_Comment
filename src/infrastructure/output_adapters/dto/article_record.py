from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.application.domain.article import Article


class ArticleRecord(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for article database records.

    Provides validation when loading data from the persistence layer.

    article_author_id is nullable — None when the author account
    has been deleted (articles are preserved via ON DELETE SET NULL).
    article_description is optional and defaults to an empty string.
    """

    model_config = ConfigDict(from_attributes=True)

    article_id: int
    article_author_id: int | None = None
    article_title: str
    article_description: str = ""
    article_content: str
    article_published_at: datetime | None = None

    def to_domain(self) -> Article:
        """
        Converts the database record into a domain Article entity.

        Returns:
            Article: The corresponding domain entity.
        """
        return Article(
            article_id=self.article_id,
            article_author_id=self.article_author_id,
            article_title=self.article_title,
            article_description=self.article_description,
            article_content=self.article_content,
            article_published_at=self.article_published_at,
        )
