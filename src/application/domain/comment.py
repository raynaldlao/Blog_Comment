from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


class Comment:
    """
    Represents a comment or a reply on an article.

    Attributes:
        comment_id (int): Unique identifier for the comment.
        comment_article_id (int): Reference to the associated article.
        comment_written_account_id (int | None): Reference to the author's account.
        comment_reply_to (int | None): Reference to a parent comment (for replies).
        comment_content (str): Text content of the comment.
        comment_posted_at (datetime): Timestamp of when the comment was posted.
        is_deleted (bool): Soft-delete flag. True if the comment has been removed.
        deleted_at (datetime | None): When the comment was soft-deleted. None if not deleted.
        edited_at (datetime | None): Last edit timestamp. None if never edited.
    """

    def __init__(
        self,
        comment_id: int,
        comment_article_id: int,
        comment_written_account_id: int | None,
        comment_reply_to: int | None,
        comment_content: str,
        comment_posted_at: datetime,
        is_deleted: bool = False,
        deleted_at: datetime | None = None,
        edited_at: datetime | None = None,
    ):
        self.comment_id = comment_id
        self.comment_article_id = comment_article_id
        self.comment_written_account_id = comment_written_account_id
        self.comment_reply_to = comment_reply_to
        self.comment_content = comment_content
        self.comment_posted_at = comment_posted_at
        self.is_deleted = is_deleted
        self.deleted_at = deleted_at
        self.edited_at = edited_at

@dataclass
class CommentWithAuthor:
    """
    Read Model that combines a Comment domain entity with its author's username
    and optional avatar file ID.

    Attributes:
        comment (Comment): The underlying comment domain entity.
        author_name (str): The display name of the comment author.
        author_avatar_file_id (str | None): UUID of the author's avatar file, or None.
    """
    comment: Comment
    author_name: str
    author_avatar_file_id: str | None = None

@dataclass
class CommentNode:
    """
    Recursive tree node for N-level nested comment threading.
    """
    comment: CommentWithAuthor
    replies: list[CommentNode] = field(default_factory=list)
    depth: int = 0

