from datetime import datetime


class Comment:
    """
    Represents a comment or a reply on an article.

    Attributes:
        comment_id (int): Unique identifier for the comment.
        comment_article_id (int): Reference to the associated article.
        comment_written_account_id (int): Reference to the author's account.
        comment_reply_to (int | None): Reference to a parent comment (for replies).
        comment_content (str): Text content of the comment.
        comment_posted_at (datetime): Timestamp of when the comment was posted.
    """

    def __init__(
        self,
        comment_id: int,
        comment_article_id: int,
        comment_written_account_id: int,
        comment_reply_to: int | None,
        comment_content: str,
        comment_posted_at: datetime,
    ):
        """
        Initialize a comment or reply.

        Args:
            comment_id (int): Unique identifier for the comment.
            comment_article_id (int): Reference to the associated article.
            comment_written_account_id (int): Reference to the author's account.
            comment_reply_to (int | None): Reference to a parent comment (for replies).
            comment_content (str): Text content of the comment.
            comment_posted_at (datetime): Timestamp of when the comment was posted.
        """
        self.comment_id = comment_id
        self.comment_article_id = comment_article_id
        self.comment_written_account_id = comment_written_account_id
        self.comment_reply_to = comment_reply_to
        self.comment_content = comment_content
        self.comment_posted_at = comment_posted_at
