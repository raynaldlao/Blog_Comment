from pydantic import BaseModel, Field


class CommentRequest(BaseModel):
    """
    Data Transfer Object representing the request to create or reply to a comment.
    Ensures that content is not empty and follows SQLAlchemy constraints.
    """

    content: str = Field(
        ...,
        min_length=1,
        description="The text content of the comment. Required (NOT NULL)."
    )
