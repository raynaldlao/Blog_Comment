from pydantic import BaseModel, Field, constr


class ArticleRequest(BaseModel):
    """
    Data Transfer Object representing the request to create or update an article.
    Validates incoming data constraints at the web boundary.
    """
    title: constr(strip_whitespace=True, min_length=3, max_length=150) = Field(
        ..., description="The title of the article. Must be between 3 and 150 characters."
    )
    content: constr(strip_whitespace=True, min_length=10) = Field(
        ..., description="The main content of the article. Must be at least 10 characters."
    )
