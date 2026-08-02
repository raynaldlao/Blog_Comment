from datetime import datetime

from src.application.domain.article import Article
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository


class InMemoryArticleRepository(ArticleRepository):
    """
    In-memory implementation of the ArticleRepository.
    Uses a dictionary to store articles, primarily for unit testing.

    When an AccountRepository is provided, the search and count_search
    methods also match articles by the author's username. If no account
    repository is given, they only match by title and description.
    """

    def __init__(self, account_repository: AccountRepository | None = None):
        """
        Initializes the repository with an empty internal dictionary and ID counter.

        Args:
            account_repository: Optional AccountRepository for author
                username search support. When None, search only matches
                by title and description.
        """
        self._articles: dict[int, Article] = {}
        self._next_id = 1
        self._account_repository: AccountRepository | None = account_repository

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

    def search(self, query: str, page: int, per_page: int) -> list[Article]:
        """
        Searches articles by title, description, or author username using a
        case-insensitive substring match against the in-memory dictionary.

        When an AccountRepository was provided at init, the author's
        username is also searched via get_all(). Otherwise, only title
        and description are matched.

        Args:
            query: The search term to match against article titles,
                descriptions, or author usernames.
            page: The page number (1-indexed).
            per_page: The number of items per page.

        Returns:
            A list of Article domain entities matching the search query
            for the given page, ordered by publication date descending.
        """
        lower_query = query.lower()

        matching_author_ids: set[int] = set()
        if self._account_repository is not None:
            for account in self._account_repository.get_all():
                if lower_query in account.account_username.lower():
                    matching_author_ids.add(account.account_id)

        filtered_articles = [
            article for article in self._articles.values()
            if lower_query in article.article_title.lower()
            or (article.article_description
                and lower_query in article.article_description.lower())
            or (article.article_author_id is not None
                and article.article_author_id in matching_author_ids)
        ]
        sorted_articles = sorted(
            filtered_articles,
            key=lambda article: article.article_published_at or datetime.min,
            reverse=True,
        )
        start_index = (page - 1) * per_page
        return sorted_articles[start_index:start_index + per_page]

    def count_search(self, query: str) -> int:
        """
        Counts articles matching a search query by title, description,
        or author username.

        When an AccountRepository was provided at init, the author's
        username is also searched via get_all(). Otherwise, only title
        and description are matched.

        Args:
            query: The search term to match against article titles,
                descriptions, or author usernames.

        Returns:
            The total number of matching articles.
        """
        lower_query = query.lower()

        matching_author_ids: set[int] = set()
        if self._account_repository is not None:
            for account in self._account_repository.get_all():
                if lower_query in account.account_username.lower():
                    matching_author_ids.add(account.account_id)

        return sum(
            1 for article in self._articles.values()
            if lower_query in article.article_title.lower()
            or (article.article_description
                and lower_query in article.article_description.lower())
            or (article.article_author_id is not None
                and article.article_author_id in matching_author_ids)
        )
