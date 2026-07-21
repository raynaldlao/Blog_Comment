from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from src.application.domain.article import Article
from src.application.output_ports.article_repository import ArticleRepository
from src.infrastructure.output_adapters.dto.article_record import ArticleRecord
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
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
        Persists an article to the database.
        If the article has an ID of 0, a new record is created (INSERT).
        If the article has a valid ID, the existing record is updated (UPDATE).

        Args:
            article (Article): The Article domain entity to persist.
        """
        if article.article_id and article.article_id > 0:
            self._session.query(ArticleModel).filter_by(
                article_id=article.article_id,
            ).update({
                ArticleModel.article_title: article.article_title,
                ArticleModel.article_description: article.article_description,
                ArticleModel.article_content: article.article_content,
                ArticleModel.article_edited_at: article.article_edited_at,
            })
            self._session.commit()
            return

        model = ArticleModel()
        model.article_author_id = article.article_author_id
        model.article_title = article.article_title
        model.article_description = article.article_description
        model.article_content = article.article_content
        model.article_edited_at = article.article_edited_at
        self._session.add(model)
        self._session.commit()
        article.article_id = model.article_id

    def delete(self, article: Article) -> None:
        """
        Deletes a given article from the database.

        Args:
            article (Article): The Article domain entity to delete.
        """
        self._session.query(ArticleModel).filter_by(
            article_id=article.article_id,
        ).delete()
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

    def search(self, query: str, page: int, per_page: int) -> list[Article]:
        """
        Searches articles by title, description, or author username using a
        case-insensitive ILIKE match on the database.

        Args:
            query: The search term to match against article titles,
                descriptions, or author usernames.
            page: The page number (1-indexed).
            per_page: The number of items per page.

        Returns:
            A list of Article domain entities matching the search query
            for the given page, ordered by publication date descending.
        """
        like = f"%{query}%"
        offset = (page - 1) * per_page
        models = (
            self._session.query(ArticleModel)
            .outerjoin(
                AccountModel,
                ArticleModel.article_author_id == AccountModel.account_id,
            )
            .filter(
                or_(
                    ArticleModel.article_title.ilike(like),
                    ArticleModel.article_description.ilike(like),
                    AccountModel.account_username.ilike(like),
                )
            )
            .order_by(desc(ArticleModel.article_published_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def count_search(self, query: str) -> int:
        """
        Counts articles matching a search query across title, description,
        or author username.

        Args:
            query: The search term to match against article titles,
                descriptions, or author usernames.

        Returns:
            The total number of articles matching the query.
        """
        like = f"%{query}%"
        return (
            self._session.query(ArticleModel)
            .outerjoin(
                AccountModel,
                ArticleModel.article_author_id == AccountModel.account_id,
            )
            .filter(
                or_(
                    ArticleModel.article_title.ilike(like),
                    ArticleModel.article_description.ilike(like),
                    AccountModel.account_username.ilike(like),
                )
            )
            .count()
        )
