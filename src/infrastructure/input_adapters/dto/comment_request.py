from pydantic import BaseModel, Field, field_validator


class CommentRequest(BaseModel):
    """
    Data Transfer Object representing the request to create or reply to a comment.
    Ensures that content is not empty and follows SQLAlchemy constraints.
    """

    content: str = Field(
        ...,
        min_length=1,
        description="The text content of the comment. Required, max 5000 characters."
    )

    @field_validator("content")
    @classmethod
    def check_content_length(cls, v: str) -> str:
        if len(v) > 5000:
            raise ValueError("Comment is too long. Maximum 5000 characters.")
        return v
