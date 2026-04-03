from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.application.domain.article import Article
from src.application.output_ports.article_repository import ArticleRepository
from src.infrastructure.output_adapters.dto.article_record import ArticleRecord
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel


class SqlAlchemyArticleAdapter(ArticleRepository):
    """
    SQLAlchemy-based implementation of the ArticleRepository port.

    This adapter manages the persistence and retrieval of Article domain entities
    using SQLAlchemy ORM and the PostgreSQL database.
    """

    def __init__(self, session: Session):
        """
        Initializes the adapter with a SQLAlchemy session.

        Args:
            session (Session): An active SQLAlchemy database session.
        """
        self._session = session

    def _to_domain(self, model: ArticleModel) -> Article:
        """
        Maps a SQLAlchemy ORM model to a Domain Entity via a DTO.

        Args:
            model (ArticleModel): The database record to convert.

        Returns:
            Article: The converted Domain Entity.
        """
        record = ArticleRecord.model_validate(model)
        return record.to_domain()

    def get_all_ordered_by_date_desc(self) -> list[Article]:
        """
        Retrieves all articles ordered by publication date (descending).

        Returns:
            list[Article]: A list of all Article domain entities.
        """
        models = (
            self._session.query(ArticleModel)
            .order_by(desc(ArticleModel.article_published_at))
            .all()
        )
        return [self._to_domain(model) for model in models]

    def get_by_id(self, article_id: int) -> Article | None:
        """
        Retrieves a single article by its ID.

        Args:
            article_id (int): The unique identifier of the article.

        Returns:
            Article | None: The Article domain entity if found, None otherwise.
        """
        model = self._session.get(ArticleModel, article_id)
        if model is None:
            return None
        return self._to_domain(model)

    def save(self, article: Article) -> None:
        """
        Saves a new article to the database.

        Args:
            article (Article): The Article domain entity to save.
        """
        model = ArticleModel()
        model.article_author_id = article.article_author_id
        model.article_title = article.article_title
        model.article_content = article.article_content
        self._session.add(model)
        self._session.commit()

    def delete(self, article: Article) -> None:
        """
        Deletes a given article from the database.

        Args:
            article (Article): The Article domain entity to delete.
        """
        model = self._session.get(ArticleModel, article.article_id)
        if model:
            self._session.delete(model)
            self._session.commit()

    def get_paginated(self, page: int, per_page: int) -> list[Article]:
        """
        Retrieves a paginated list of articles.

        Args:
            page (int): The requested page number (1-indexed).
            per_page (int): The number of articles to return per page.

        Returns:
            list[Article]: A list of Article domain entities for the specified page.
        """
        offset = (page - 1) * per_page
        models = (
            self._session.query(ArticleModel)
            .order_by(desc(ArticleModel.article_published_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )

        return [self._to_domain(model) for model in models]

    def count_all(self) -> int:
        """
        Retrieves the total number of articles.

        Returns:
            int: The total count of articles in the database.
        """
        return self._session.query(ArticleModel).count()
