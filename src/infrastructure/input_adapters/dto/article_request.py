from pydantic import BaseModel, Field


class ArticleRequest(BaseModel):
    """
    Data Transfer Object representing the request to create or update an article.
    Synchronised with SQLAlchemy model constraints (Text, nullable=False).
    Using min_length=1 to enforce that 'NOT NULL' fields are not empty.
    description is optional, defaults to empty string, limited to 300 characters.
    """
    title: str = Field(
        ..., min_length=1, description="The title of the article. Required (NOT NULL)."
    )
    content: str = Field(
        ..., min_length=1, description="The main content of the article. Required (NOT NULL)."
    )
    description: str = Field(
        "", max_length=300, description="Short description displayed in article list. Optional."
    )
