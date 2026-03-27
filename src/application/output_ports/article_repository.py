from abc import ABC, abstractmethod

from src.application.domain.article import Article


class ArticleRepository(ABC):
    """
    Output port defining the contract for Article persistence operations.
    Any infrastructure adapter (SQLAlchemy, MongoDB, etc.) must implement
    this interface.
    """

    @abstractmethod
    def get_all_ordered_by_date_desc(self) -> list[Article]:
        """
        Retrieves all articles ordered by publication date (descending).

        Returns:
            list[Article]: A list of Article domain entities.
        """
        pass

    @abstractmethod
    def get_by_id(self, article_id: int) -> Article | None:
        """
        Retrieves a single article by its ID.

        Args:
            article_id (int): The unique identifier of the article.

        Returns:
            Article | None: The Article domain entity if found,
            None otherwise.
        """
        pass

    @abstractmethod
    def save(self, article: Article) -> None:
        """
        Saves a new article to the database.

        Args:
            article (Article): The Article domain entity to save.
        """
        pass

    @abstractmethod
    def delete(self, article: Article) -> None:
        """
        Deletes a given article.

        Args:
            article (Article): The Article domain entity to delete.
        """
        pass
