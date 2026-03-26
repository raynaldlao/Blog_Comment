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
        account = self.account_repository.get_by_id(author_id)
        valid_roles = ["admin", "author"]
        if not account or author_role not in valid_roles:
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
