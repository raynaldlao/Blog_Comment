from abc import ABC, abstractmethod

from src.application.domain.article import Article, ArticleDetailView, ArticleWithAuthor


class ArticleManagementPort(ABC):
    """
    Input port (interface) defining the business operations for article management.
    This serves as the API of the Core, to be used by input adapters (Web, CLI, etc.).
    """

    @abstractmethod
    def create_article(self, title: str, content: str, author_id: int, author_role: str, description: str = "") -> Article:
        """
        Creates a new article if the user has sufficient permissions.

        Args:
            title (str): The title of the new article.
            content (str): The body content of the new article.
            author_id (int): The unique identifier of the user creating the article.
            author_role (str): The role of the user.
            description (str): Short description displayed in article list. Optional.

        Returns:
            Article: The newly created Article domain entity.

        Raises:
            AccountNotFoundError: If the author account is not found.
            InsufficientPermissionsError: If the user is not an author or admin.
            AccountBannedError: If the account is banned.
        """
        pass

    @abstractmethod
    def get_by_id(self, article_id: int) -> Article | None:
        """
        Retrieves a single article by its unique identifier.

        Args:
            article_id (int): The unique identifier of the article.

        Returns:
            Article | None: The Article domain entity if found, None otherwise.
        """
        pass

    @abstractmethod
    def update_article(self, article_id: int, user_id: int, title: str, content: str, description: str = "") -> Article:
        """
        Updates an existing article ensuring the requester is the original author.

        Args:
            article_id (int): ID of the article to update.
            user_id (int): ID of the user requesting the update.
            title (str): New title for the article.
            content (str): New content for the article.
            description (str): Short description displayed in article list. Optional.

        Returns:
            Article: The updated Article domain entity.

        Raises:
            AccountNotFoundError: If the user account is not found.
            InsufficientPermissionsError: If the user is not an author or admin.
            AccountBannedError: If the account is banned.
            ArticleNotFoundError: If the article does not exist.
            OwnershipError: If the user is not the author (and not admin).
        """
        pass

    @abstractmethod
    def delete_article(self, article_id: int, user_id: int) -> bool:
        """
        Deletes an article. Only the original author or an admin can delete it.

        Args:
            article_id (int): ID of the article to delete.
            user_id (int): ID of the user requesting the deletion.

        Returns:
            bool: True if deletion was successful.

        Raises:
            AccountNotFoundError: If the user account is not found.
            InsufficientPermissionsError: If the user is not an author or admin.
            AccountBannedError: If the account is banned.
            ArticleNotFoundError: If the article does not exist.
            OwnershipError: If the user is not the author (and not admin).
        """
        pass

    @abstractmethod
    def get_paginated_articles(self, page: int, per_page: int) -> list[ArticleWithAuthor]:
        """
        Retrieves a paginated list of articles along with their authors' usernames.

        Args:
            page (int): The page number requested (1-indexed).
            per_page (int): The number of items to display per page.

        Returns:
            list[ArticleWithAuthor]: A list of Read Models combining articles and their authors.
        """
        pass

    @abstractmethod
    def get_total_count(self) -> int:
        """
        Retrieves the total number of articles.

        Returns:
            int: The total count of all articles.
        """
        pass

    @abstractmethod
    def get_author_name(self, author_id: int | None) -> str:
        """
        Retrieves the username of an author by their unique identifier.

        Args:
            author_id (int | None): The unique identifier of the author.
                None when the author's account has been deleted.

        Returns:
            str: The username of the author, 'Anonymous' if the account was
            deleted, or 'Unknown' if not found.
        """
        pass

    @abstractmethod
    def get_article_with_comments(self, article_id: int) -> ArticleDetailView:
        """
        Orchestrates the retrieval of an article, its associated comments, and author information.

        Args:
            article_id (int): ID of the article to retrieve.

        Returns:
            ArticleDetailView: A Read Model for the complete article detail page.

        Raises:
            ArticleNotFoundError: If the article does not exist.
        """
        pass

    @abstractmethod
    def search_articles(self, query: str, page: int, per_page: int) -> list[ArticleWithAuthor]:
        """
        Searches articles by title or description.

        Args:
            query: The search term to match against article titles
                and descriptions.
            page: The page number (1-indexed).
            per_page: The number of items per page.

        Returns:
            A list of ArticleWithAuthor read models matching the query
            for the given page, ordered by publication date descending.
        """
        pass

    @abstractmethod
    def count_search(self, query: str) -> int:
        """
        Counts articles matching a search query.

        Args:
            query: The search term to match against article titles
                and descriptions.

        Returns:
            The total number of matching articles.
        """
        pass
