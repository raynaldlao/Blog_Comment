from dataclasses import dataclass, field
from datetime import datetime

from src.application.domain.comment import CommentThreadView


class Article:
    """
    Represents a blog article.

    Attributes:
        article_id (int): Unique identifier for the article.
        article_author_id (int): Reference to the author's Account.
        article_title (str): Title of the article.
        article_content (str): Full text content of the article.
        article_published_at (datetime): Timestamp of publication.
    """

    def __init__(
        self,
        article_id: int,
        article_author_id: int,
        article_title: str,
        article_content: str,
        article_published_at: datetime | None,
    ):
        """
        Initialize a blog article.

        Args:
            article_id (int): Unique identifier for the article.
            article_author_id (int): Reference to the author's Account.
            article_title (str): Title of the article.
            article_content (str): Full text content of the article.
            article_published_at (datetime): Timestamp of publication.
        """
        self.article_id = article_id
        self.article_author_id = article_author_id
        self.article_title = article_title
        self.article_content = article_content
        self.article_published_at = article_published_at

@dataclass
class ArticleWithAuthor:
    """
    Read Model that combines an Article domain entity with its author's username.
    """
    article: Article
    author_name: str

@dataclass
class ArticleDetailView:
    """
    Read Model for the article detail page.
    Encapsulates an article with its author and threaded comments.
    """
    article_with_author: ArticleWithAuthor
    threaded_comments: CommentThreadView = field(default_factory=CommentThreadView)
