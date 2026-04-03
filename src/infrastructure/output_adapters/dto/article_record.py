from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.application.domain.article import Article


class ArticleRecord(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for article database records.

    Provides validation when loading data from the persistence layer.
    """

    model_config = ConfigDict(from_attributes=True)

    article_id: int
    article_author_id: int
    article_title: str
    article_content: str
    article_published_at: datetime

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
            article_content=self.article_content,
            article_published_at=self.article_published_at,
        )
