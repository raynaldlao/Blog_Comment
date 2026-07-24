import re

from pydantic import BaseModel, Field, field_validator

from blog_exceptions import CommentEmptyError, CommentTooLongError


class CommentRequest(BaseModel):
    """
    Data Transfer Object representing the request to create or reply to a comment.
    Ensures that content contains at least one non-whitespace character after
    stripping HTML tags, and respects the DB VARCHAR(5000) limit.
    """

    content: str = Field(
        ...,
        min_length=1,
        description="The text content of the comment. Required, max 5000 characters."
    )

    @field_validator("content")
    @classmethod
    def check_content_length(cls, v: str) -> str:
        """
        Validates comment content is not empty after stripping HTML tags
        and does not exceed the DB VARCHAR(5000) limit.

        Raises:
            CommentEmptyError: If content has no non-whitespace characters.
            CommentTooLongError: If content exceeds 5000 characters.
        """
        text = re.sub(r"<[^>]+>", "", v).strip()
        if len(text) < 1:
            raise CommentEmptyError("Comment cannot be empty.")
        if len(v) > 5000:
            raise CommentTooLongError("Comment is too long. Maximum 5000 characters.")
        return v
