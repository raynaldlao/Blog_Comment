import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict


def _blocks_to_plain_text(blocks_json: str) -> str:
    try:
        blocks = json.loads(blocks_json)
    except (json.JSONDecodeError, TypeError):
        return blocks_json

    if not isinstance(blocks, list):
        return blocks_json

    texts = []
    for block in blocks:
        content = block.get("content")
        if isinstance(content, list):
            for node in content:
                if isinstance(node, dict) and "text" in node:
                    texts.append(node["text"])
        elif isinstance(content, str):
            texts.append(content)
    return " ".join(texts)


class ArticleResponse(BaseModel):
    """
    Data Transfer Object used to send article data to the UI.
    Protects the Domain entity from being exposed directly to the templates.

    Attributes:
        article_author_id (int | None): Reference to the author's Account.
            None when the author's account has been deleted.
        author_avatar_file_id (str | None): UUID of the author's avatar file, or None.
    """
    model_config = ConfigDict(from_attributes=True)

    article_id: int
    article_author_id: int | None = None
    author_username: str = "Unknown"
    author_avatar_file_id: str | None = None
    article_title: str
    article_content: str
    article_published_at: datetime | None = None
    meta_description: str = ""

    @classmethod
    def from_domain(cls, article, author_username: str = "Unknown", author_avatar_file_id: str | None = None):
        plain_text = _blocks_to_plain_text(article.article_content).replace("\n", " ").strip()
        limit_character = 155
        if len(plain_text) > limit_character:
            meta = f"{plain_text[:limit_character]}..."
        else:
            meta = plain_text

        return cls(
            article_id=article.article_id,
            article_author_id=article.article_author_id,
            author_username=author_username,
            author_avatar_file_id=author_avatar_file_id,
            article_title=article.article_title,
            article_content=article.article_content,
            article_published_at=article.article_published_at,
            meta_description=meta
        )
