from abc import ABC, abstractmethod

from src.application.domain.article import Article


class ArticleManagementPort(ABC):
    """
    Input port (interface) defining the business operations for article management.
    This serves as the API of the Core, to be used by input adapters (Web, CLI, etc.).
    """

    @abstractmethod
    def create_article(self, title: str, content: str, author_id: int, author_role: str) -> Article | str:
        """
        Creates a new article if the user has sufficient permissions.

        Args:
            title (str): The title of the new article.
            content (str): The body content of the new article.
            author_id (int): The unique identifier of the user creating the article.
            author_role (str): The role of the user.

        Returns:
            Article | str: The newly created Article domain entity,
            or an error message string if unauthorized or account not found.
        """
        pass

    @abstractmethod
    def get_all_ordered_by_date_desc(self) -> list[Article]:
        """
        Retrieves all articles ordered by their publication date in descending order.

        Returns:
            list[Article]: A list of Article domain entities.
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
    def update_article(self, article_id: int, user_id: int, title: str, content: str) -> Article | str:
        """
        Updates an existing article ensuring the requester is the original author.

        Args:
            article_id (int): ID of the article to update.
            user_id (int): ID of the user requesting the update.
            title (str): New title for the article.
            content (str): New content for the article.

        Returns:
            Article | str: The updated Article domain entity,
            or an error message string if not found or unauthorized.
        """
        pass

    @abstractmethod
    def delete_article(self, article_id: int, user_id: int) -> bool | str:
        """
        Deletes an article. Only the original author or an admin can delete it.

        Args:
            article_id (int): ID of the article to delete.
            user_id (int): ID of the user requesting the deletion.

        Returns:
            bool | str: True if deletion was successful, or an error message string.
        """
        pass

    @abstractmethod
    def get_paginated_articles(self, page: int, per_page: int) -> list[Article]:
        """
        Retrieves a paginated list of articles.

        Args:
            page (int): The page number requested (1-indexed).
            per_page (int): The number of items to display per page.

        Returns:
            list[Article]: A list of Article domain entities for the requested page.
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
