from dataclasses import dataclass, field
from datetime import datetime

from src.application.domain.comment import CommentNode


class Article:
    """
    Represents a blog article.

    Attributes:
        article_id (int): Unique identifier for the article.
        article_author_id (int | None): Reference to the author's Account.
            None when the author's account has been deleted.
        article_title (str): Title of the article.
        article_description (str): Short description shown in article list.
        article_content (str): Full text content of the article.
        article_published_at (datetime): Timestamp of publication.
    """

    def __init__(
        self,
        article_id: int,
        article_author_id: int | None,
        article_title: str,
        article_content: str,
        article_published_at: datetime | None,
        article_description: str = "",
    ):
        """
        Initialize a blog article.

        Args:
            article_id (int): Unique identifier for the article.
            article_author_id (int | None): Reference to the author's Account.
                None when the author's account has been deleted.
            article_title (str): Title of the article.
            article_content (str): Full text content of the article.
            article_published_at (datetime): Timestamp of publication.
            article_description (str): Short description displayed in article
                list. Optional, defaults to empty string.
        """
        self.article_id = article_id
        self.article_author_id = article_author_id
        self.article_title = article_title
        self.article_description = article_description
        self.article_content = article_content
        self.article_published_at = article_published_at

@dataclass
class ArticleWithAuthor:
    """
    Read Model that combines an Article domain entity with its author's username
    and optional avatar file ID.

    Attributes:
        article (Article): The underlying article domain entity.
        author_name (str): The display name of the article author.
        author_avatar_file_id (str | None): UUID of the author's avatar file, or None.
    """
    article: Article
    author_name: str
    author_avatar_file_id: str | None = None

@dataclass
class ArticleDetailView:
    """
    Read Model for the article detail page.
    Encapsulates an article with its author and nested comments.
    """
    article_with_author: ArticleWithAuthor
    nested_comments: list[CommentNode] = field(default_factory=list)
