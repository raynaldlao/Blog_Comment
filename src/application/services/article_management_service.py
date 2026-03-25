from src.application.domain.article import Article
from src.application.output_ports.article_repository import ArticleRepository


class ArticleManagementService:
    """
    Service responsible for business logic operations related to Articles.
    Depends on the ArticleRepository output port for data access.
    """

    def __init__(self, article_repository: ArticleRepository):
        """
        Initialize the service with an ArticleRepository (Dependency Injection).

        Args:
            article_repository (ArticleRepository): The repository port
            for article data access.
        """
        self.article_repository = article_repository

    def create_article(self, title: str, content: str, author_id: int) -> Article:
        """
        Creates a new article and saves it via the repository.

        Args:
            title (str): The title of the new article.
            content (str): The body content of the new article.
            author_id (int): The unique identifier of the user creating the article.

        Returns:
            Article: The newly created Article domain entity.
        """
        new_article = Article(
            article_id=0,
            article_author_id=author_id,
            article_title=title,
            article_content=content,
            article_published_at=None,
        )

        self.article_repository.save(new_article)
        return new_article

    def get_all_ordered_by_date(self) -> list[Article]:
        """
        Retrieves all articles ordered by their publication date.

        Returns:
            list[Article]: A list of Article domain entities.
        """
        return self.article_repository.get_all_ordered_by_date()

    def get_by_id(self, article_id: int) -> Article | None:
        """
        Retrieves a single article by its ID.

        Args:
            article_id (int): The unique identifier of the article.

        Returns:
            Article | None: The Article domain entity if found, None otherwise.
        """
        return self.article_repository.get_by_id(article_id)
