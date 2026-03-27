from src.application.domain.account import Account
from src.application.domain.article import Article
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository


class ArticleManagementService:
    """
    Service responsible for business logic operations related to Articles.
    Depends on the ArticleRepository and AccountRepository output ports.
    """

    def __init__(self, article_repository: ArticleRepository, account_repository: AccountRepository):
        """
        Initialize the service with repositories (Dependency Injection).

        Args:
            article_repository (ArticleRepository): Port for article data.
            account_repository (AccountRepository): Port for account data.
        """
        self.article_repository = article_repository
        self.account_repository = account_repository

    def _get_authorized_account(self, user_id: int) -> Account | None:
        """
        Checks if a user exists and has the required permissions (admin or author).

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            Account | None: The Account domain entity if authorized, None otherwise.
        """
        account = self.account_repository.get_by_id(user_id)
        valid_roles = ["admin", "author"]
        if not account or account.account_role not in valid_roles:
            return None
        return account

    def create_article(self, title: str, content: str, author_id: int, author_role: str) -> Article | None:
        """
        Creates a new article and saves it via the repository if the account exists and the user has
        the correct permissions.

        Args:
            title (str): The title of the new article.
            content (str): The body content of the new article.
            author_id (int): The unique identifier of the user creating the article.
            author_role (str): The role of the user (e.g. 'admin', 'author', 'user').

        Returns:
            Article | None: The newly created Article domain entity,
            or None if unauthorized or account not found.
        """
        if not self._get_authorized_account(author_id):
            return None

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

    def update_article(self, article_id: int, user_id: int, title: str, content: str) -> Article | None:
        """
        Updates an existing article ensuring the requester is the original author.

        Args:
            article_id (int): ID of the article to update.
            user_id (int): ID of the user requesting the update.
            title (str): New title for the article.
            content (str): New content for the article.

        Returns:
            Article | None: The updated Article domain entity,
            or None if not found or unauthorized.
        """
        article = self.article_repository.get_by_id(article_id)
        if not article or article.article_author_id != user_id:
            return None

        if not self._get_authorized_account(user_id):
            return None

        article.article_title = title
        article.article_content = content
        return article
