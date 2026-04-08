from src.application.domain.account import Account, AccountRole
from src.application.domain.article import Article
from src.application.input_ports.article_management import ArticleManagementPort
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository


class ArticleService(ArticleManagementPort):
    """
    Implements the ArticleManagementPort input port.
    Handles all business logic operations related to Articles.
    Depends on the ArticleRepository and AccountRepository output ports
    for data persistence, injected via the constructor.
    """

    def __init__(self, article_repository: ArticleRepository, account_repository: AccountRepository):
        """
        Initialize the service via Dependency Injection.

        Args:
            article_repository (ArticleRepository): Port for article data access.
            account_repository (AccountRepository): Port for account data access.
        """
        self.article_repository = article_repository
        self.account_repository = account_repository

    def _get_account_if_author_or_admin(self, user_id: int) -> Account | str:
        """
        Checks if a user exists and has the required permissions (admin or author).

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            Account | str: The Account domain entity if authorized, or an error message string.
        """
        account = self.account_repository.get_by_id(user_id)
        if not account:
            # TODO: Raise AccountNotFoundException
            return "Account not found."

        if account.account_role not in [AccountRole.ADMIN, AccountRole.AUTHOR]:
            # TODO: Raise InsufficientPermissionsException
            return "Insufficient permissions."

        return account

    def create_article(self, title: str, content: str, author_id: int, author_role: str) -> Article | str:
        """
        Creates a new article and saves it via the repository if the account exists and the user has
        the correct permissions.

        Args:
            title (str): The title of the new article.
            content (str): The body content of the new article.
            author_id (int): The unique identifier of the user creating the article.
            author_role (AccountRole): The role of the user.

        Returns:
            Article | str: The newly created Article domain entity,
            or an error message string if unauthorized or account not found.
        """
        account_or_error = self._get_account_if_author_or_admin(author_id)
        if isinstance(account_or_error, str):
            return account_or_error

        new_article = Article(
            article_id=0,
            article_author_id=author_id,
            article_title=title,
            article_content=content,
            article_published_at=None,
        )

        self.article_repository.save(new_article)
        return new_article

    def get_all_ordered_by_date_desc(self) -> list[Article]:
        """
        Retrieves all articles ordered by their publication date.

        Returns:
            list[Article]: A list of Article domain entities.
        """
        return self.article_repository.get_all_ordered_by_date_desc()

    def get_by_id(self, article_id: int) -> Article | None:
        """
        Retrieves a single article by its ID.

        Args:
            article_id (int): The unique identifier of the article.

        Returns:
            Article | None: The Article domain entity if found, None otherwise.
        """
        return self.article_repository.get_by_id(article_id)

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
        account_or_error = self._get_account_if_author_or_admin(user_id)
        if isinstance(account_or_error, str):
            return account_or_error

        article = self.article_repository.get_by_id(article_id)
        if not article:
            # TODO: Raise ArticleNotFoundException
            return "Article not found."

        if article.article_author_id != user_id:
            # TODO: Raise OwnershipException
            return "Unauthorized : You are not the author of this article."

        article.article_title = title
        article.article_content = content
        self.article_repository.save(article)
        return article

    def delete_article(self, article_id: int, user_id: int) -> bool | str:
        """
        Deletes an article. Only the original author or an admin can delete it.

        Args:
            article_id (int): ID of the article to delete.
            user_id (int): ID of the user requesting the deletion.

        Returns:
            bool | str: True if deletion was successful, or an error message string.
        """
        account_or_error = self._get_account_if_author_or_admin(user_id)
        if isinstance(account_or_error, str):
            return account_or_error

        account: Account = account_or_error
        article = self.article_repository.get_by_id(article_id)
        if not article:
            # TODO: Raise ArticleNotFoundException
            return "Article not found."

        if account.account_role != AccountRole.ADMIN and article.article_author_id != user_id:
            # TODO: Raise OwnershipException
            return "Unauthorized : Only authors or admins can delete articles."

        self.article_repository.delete(article)
        return True

    def get_paginated_articles(self, page: int = 1, per_page: int = 10) -> list[Article]:
        """
        Retrieves a paginated list of articles.

        Args:
            page (int): The page number requested (1-indexed). Defaults to 1.
            per_page (int): The number of items to display per page. Defaults to 10.

        Returns:
            list[Article]: A list of Article domain entities.
        """
        min_page = 1
        if page < min_page:
            page = min_page
        return self.article_repository.get_paginated(page, per_page)

    def get_total_count(self) -> int:
        """
        Retrieves the total number of articles.

        Returns:
            int: The total count of all articles.
        """
        return self.article_repository.count_all()

    def get_author_name(self, author_id: int) -> str:
        """
        Retrieves the username of an author by their unique identifier.

        Args:
            author_id (int): The unique identifier of the author.

        Returns:
            str: The username of the author, or 'Unknown' if not found.
        """
        account = self.account_repository.get_by_id(author_id)
        return account.account_username if account else "Unknown"

