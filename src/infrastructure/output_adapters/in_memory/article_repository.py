from datetime import datetime

from src.application.domain.article import Article
from src.application.output_ports.article_repository import ArticleRepository


class InMemoryArticleRepository(ArticleRepository):
    """
    In-memory implementation of the ArticleRepository.
    Uses a dictionary to store articles, primarily for unit testing.
    """

    def __init__(self):
        """
        Initializes the repository with an empty internal dictionary and ID counter.
        """
        self._articles: dict[int, Article] = {}
        self._next_id = 1

    def save(self, article: Article) -> None:
        """
        Saves a new article or updates an existing one. If the article has an ID of 0,
        it assigns the next available auto-incremented ID.

        Args:
            article (Article): The article entity to save.
        """
        if article.article_id == 0:
            article.article_id = self._next_id
            self._next_id += 1
        self._articles[article.article_id] = article

    def get_by_id(self, article_id: int) -> Article | None:
        """
        Retrieves a single article by its ID.

        Args:
            article_id (int): The unique identifier of the article.

        Returns:
            Article | None: The Article domain entity if found, None otherwise.
        """
        return self._articles.get(article_id)

    def get_all_ordered_by_date_desc(self) -> list[Article]:
        """
        Retrieves all articles ordered by publication date (descending).

        Returns:
            list[Article]: A sorted list of Article domain entities.
        """
        return sorted(list(self._articles.values()), key=lambda a: a.article_published_at or datetime.min, reverse=True)

    def get_paginated(self, page: int, per_page: int) -> list[Article]:
        """
        Retrieves a paginated list of articles, ordered by date descending.

        Args:
            page (int): The page number (1-indexed).
            per_page (int): The number of items per page.

        Returns:
            list[Article]: A slice of the sorted Article list.
        """
        sorted_articles = self.get_all_ordered_by_date_desc()
        start = (page - 1) * per_page
        end = start + per_page
        return sorted_articles[start:end]

    def count_all(self) -> int:
        """
        Retrieves the total number of articles stored in memory.

        Returns:
            int: The total count of articles.
        """
        return len(self._articles)

    def delete(self, article: Article) -> None:
        """
        Deletes a given article from memory.

        Args:
            article (Article): The Article domain entity to delete.
        """
        if article.article_id in self._articles:
            del self._articles[article.article_id]
