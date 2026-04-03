from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.application.domain.comment import Comment


class CommentRecord(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for comment database records.

    Provides validation when loading data from the persistence layer.
    """

    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    comment_article_id: int
    comment_written_account_id: int
    comment_reply_to: int | None
    comment_content: str
    comment_posted_at: datetime

    def to_domain(self) -> Comment:
        """
        Converts the database record into a domain Comment entity.

        Returns:
            Comment: The corresponding domain entity.
        """
        return Comment(
            comment_id=self.comment_id,
            comment_article_id=self.comment_article_id,
            comment_written_account_id=self.comment_written_account_id,
            comment_reply_to=self.comment_reply_to,
            comment_content=self.comment_content,
            comment_posted_at=self.comment_posted_at,
        )
