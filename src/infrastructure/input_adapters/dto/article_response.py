from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict


class ArticleResponse(BaseModel):
    """
    Data Transfer Object used to send article data to the UI.
    Protects the Domain entity from being exposed directly to the templates.

    Attributes:
        article_author_id (int | None): Reference to the author's Account.
            None when the author's account has been deleted.
        author_avatar_file_id (str | None): UUID of the author's avatar file, or None.
        article_description (str): Short description displayed in article list.
            Empty string when no description was provided.
        meta_description (str): Alias for article_description, used for
            <meta name="description"> and list view excerpt.
        article_edited_at (datetime | None): Last edit timestamp. None if never edited.
        article_edited_at_formatted (str): Human-readable edit time in Europe/Paris.
            Empty string if never edited.
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
    article_edited_at_formatted: str = ""

    @staticmethod
    def _to_local_full(dt: datetime) -> str:
        """Convert a UTC datetime to a Europe/Paris formatted string for display.

        Args:
            dt (datetime): The datetime to convert (assumed UTC; naive treated as UTC).

        Returns:
            str: Formatted string like "January 27, 2023 at 13:00".
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        local = dt.astimezone(ZoneInfo("Europe/Paris"))
        return local.strftime("%B %d, %Y at %H:%M")

    @classmethod
    def from_domain(cls, article, author_username: str = "Unknown", author_avatar_file_id: str | None = None):
        """Build an ArticleResponse from a domain Article entity.

        Maps all fields from the domain object into the DTO. Formats
        article_edited_at into a human-readable Europe/Paris string.

        Args:
            article: The domain Article instance to convert.
            author_username (str): The author's display name. Defaults to "Unknown".
            author_avatar_file_id (str | None): UUID of the author's avatar file.

        Returns:
            ArticleResponse: The populated response DTO.
        """
        description = article.article_description or ""

        article_edited_at_formatted = ""
        if article.article_edited_at:
            article_edited_at_formatted = cls._to_local_full(article.article_edited_at)

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
            article_edited_at_formatted=article_edited_at_formatted,
        )
