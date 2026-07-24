from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentResponse(BaseModel):
    """
    Data Transfer Object used to send comment data to the UI.
    Protects the Domain entity from being exposed directly to the templates.

    Dates are returned as raw UTC datetimes.
    Formatting with locale-aware filters happens in the template layer.

    Attributes:
        comment_id (int): Unique identifier for the comment.
        comment_article_id (int): Reference to the associated article.
        comment_written_account_id (int | None): Reference to the author's account.
        author_username (str): Display name of the comment author.
        author_avatar_file_id (str | None): UUID of the author's avatar file, or None.
        comment_reply_to (int | None): Reference to a parent comment (for replies).
        comment_content (str): Text content of the comment.
        comment_posted_at (datetime | None): Posting timestamp in UTC.
        is_deleted (bool): Soft-delete flag.
        edited_at (datetime | None): Last edit timestamp in UTC. None if never edited.
    """
    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    comment_article_id: int
    comment_written_account_id: int | None
    author_username: str = "Unknown"
    author_avatar_file_id: str | None = None
    comment_reply_to: int | None
    comment_content: str
    comment_posted_at: datetime | None = None
    is_deleted: bool = False
    edited_at: datetime | None = None

    @classmethod
    def from_domain(cls, comment, author_username: str = "Unknown", author_avatar_file_id: str | None = None):
        """
        Helper factory to create a response DTO from a domain Comment entity.
        Maps is_deleted, deleted_at, and edited_at from the domain entity.

        If the comment's author account has been deleted (comment_written_account_id is None)
        or the comment has been soft-deleted (is_deleted is True),
        the author is set to "Anonymous". Content display is handled by the template.

        Args:
            comment: The domain Comment entity to convert.
            author_username (str): Display name of the comment author.
            author_avatar_file_id (str | None): UUID of the author's avatar file.

        Returns:
            CommentResponse: The response DTO ready for serialization.
        """
        content = comment.comment_content
        is_deleted = comment.is_deleted

        if comment.comment_written_account_id is None or is_deleted:
            author_username = "Anonymous"

        return cls(
            comment_id=comment.comment_id,
            comment_article_id=comment.comment_article_id,
            comment_written_account_id=comment.comment_written_account_id,
            author_username=author_username,
            author_avatar_file_id=author_avatar_file_id,
            comment_reply_to=comment.comment_reply_to,
            comment_content=content,
            comment_posted_at=comment.comment_posted_at,
            is_deleted=is_deleted,
            edited_at=comment.edited_at,
        )

    @classmethod
    def map_nested_tree(cls, nodes: list, depth_limit: int = 4) -> list[CommentNodeResponse]:
        """
        Maps domain CommentNode tree into DTO tree.
        Stops nesting at depth_limit - 1; deeper nodes have empty replies.

        Args:
            nodes (list[CommentNode]): Root tree nodes from domain layer.
            depth_limit (int): Max nesting depth; deeper nodes truncated.

        Returns:
            list[CommentNodeResponse]: Mapped DTO tree.
        """
        def _map(node) -> CommentNodeResponse:
            display_depth = node.depth if node.depth < depth_limit else depth_limit
            cr = cls.from_domain(node.comment.comment, node.comment.author_name, node.comment.author_avatar_file_id)
            if node.depth < depth_limit - 1:
                replies = [_map(child) for child in node.replies]
            else:
                replies = []
            return CommentNodeResponse(comment=cr, replies=replies, depth=display_depth)
        return [_map(n) for n in nodes]


@dataclass
class CommentNodeResponse:
    """
    Recursive DTO for a single node in the nested comment tree.
    """
    comment: CommentResponse
    replies: list[CommentNodeResponse] = field(default_factory=list)
    depth: int = 0
