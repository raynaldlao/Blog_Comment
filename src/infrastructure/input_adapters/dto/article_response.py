from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleResponse(BaseModel):
    """
    Data Transfer Object used to send article data to the UI.
    Protects the Domain entity from being exposed directly to the templates.

    Dates are returned as raw UTC datetimes.
    Formatting with locale-aware filters happens in the template layer.

    Attributes:
        article_id (int): Unique identifier for the article.
        article_author_id (int | None): Reference to the author's Account.
            None when the author's account has been deleted.
        author_username (str): Display name of the article author.
        author_avatar_file_id (str | None): UUID of the author's avatar file, or None.
        article_title (str): Title of the article.
        article_description (str): Short description displayed in article list.
            Empty string when no description was provided.
        article_content (str): JSON content for the BlockNote editor.
        article_published_at (datetime | None): Publication timestamp in UTC.
        meta_description (str): Alias for article_description, used for
            <meta name="description"> and list view excerpt.
        article_edited_at (datetime | None): Last edit timestamp in UTC.
            None if never edited.
    """
    model_config = ConfigDict(from_attributes=True)

    article_id: int
    article_author_id: int | None = None
    author_username: str = "Unknown"
    author_avatar_file_id: str | None = None
    article_title: str
    article_description: str = ""
    article_content: str
    article_published_at: datetime | None = None
    meta_description: str = ""
    article_edited_at: datetime | None = None

    @classmethod
    def from_domain(cls, article, author_username: str = "Unknown", author_avatar_file_id: str | None = None):
        """Build an ArticleResponse from a domain Article entity.

        Args:
            article: The domain Article instance to convert.
            author_username (str): The author's display name. Defaults to "Unknown".
            author_avatar_file_id (str | None): UUID of the author's avatar file.

        Returns:
            ArticleResponse: The populated response DTO.
        """
        description = article.article_description or ""

        return cls(
            article_id=article.article_id,
            article_author_id=article.article_author_id,
            author_username=author_username,
            author_avatar_file_id=author_avatar_file_id,
            article_title=article.article_title,
            article_description=description,
            article_content=article.article_content,
            article_published_at=article.article_published_at,
            meta_description=description,
            article_edited_at=article.article_edited_at,
        )
