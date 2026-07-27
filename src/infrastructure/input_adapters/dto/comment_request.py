from pydantic import BaseModel, Field


class CommentRequest(BaseModel):
    """
    Data Transfer Object representing the request to create or reply to a comment.
    Content length and sanitization are validated by the service layer.
    """

    content: str = Field(
        ...,
        min_length=1,
        description="The text content of the comment. Required.",
    )
