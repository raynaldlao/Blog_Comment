from pydantic import BaseModel, ConfigDict


class ArticleResponse(BaseModel):
    """
    Data Transfer Object used to send article data to the UI.
    Protects the Domain entity from being exposed directly to the templates.
    """
    model_config = ConfigDict(from_attributes=True)

    article_id: int
    article_author_id: int
    author_username: str = "Unknown"
    article_title: str
    article_content: str
    article_published_at_formatted: str = ""
    meta_description: str = ""

    @classmethod
    def from_domain(cls, article, author_username: str = "Unknown"):
        """
        Helper factory to create a response DTO from a domain Article entity.
        The meta_description is generated from the first 155 characters of the
        article content, which is the optimal length for Google search display.
        """
        formatted_date = ""
        if article.article_published_at:
            formatted_date = article.article_published_at.strftime("%B %d, %Y")

        plain_text = article.article_content.replace("\n", " ").strip()
        limit_character = 155
        if len(plain_text) > limit_character:
            meta = f"{plain_text[:limit_character]}..."
        else:
            meta = plain_text

        return cls(
            article_id=article.article_id,
            article_author_id=article.article_author_id,
            author_username=author_username,
            article_title=article.article_title,
            article_content=article.article_content,
            article_published_at_formatted=formatted_date,
            meta_description=meta
        )
