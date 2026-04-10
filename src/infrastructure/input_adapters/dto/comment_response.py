from pydantic import BaseModel, ConfigDict


class CommentResponse(BaseModel):
    """
    Data Transfer Object used to send comment data to the UI.
    Protects the Domain entity from being exposed directly to the templates.
    Handles formatting of complex types like dates.
    """
    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    comment_article_id: int
    comment_written_account_id: int
    author_username: str = "Unknown"
    comment_reply_to: int | None
    comment_content: str
    comment_posted_at_formatted: str = ""

    @classmethod
    def from_domain(cls, comment, author_username: str = "Unknown"):
        """
        Helper factory to create a response DTO from a domain Comment entity.
        Formats the posting date into a reader-friendly string.

        Args:
            comment (Comment): The domain comment entity.
            author_username (str): The username of the comment author.

        Returns:
            CommentResponse: The initialized DTO.
        """
        formatted_date = ""
        if comment.comment_posted_at:
            formatted_date = comment.comment_posted_at.strftime("%B %d, %Y at %H:%M")

        return cls(
            comment_id=comment.comment_id,
            comment_article_id=comment.comment_article_id,
            comment_written_account_id=comment.comment_written_account_id,
            author_username=author_username,
            comment_reply_to=comment.comment_reply_to,
            comment_content=comment.comment_content,
            comment_posted_at_formatted=formatted_date
        )
