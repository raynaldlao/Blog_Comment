from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict


class CommentResponse(BaseModel):
    """
    Data Transfer Object used to send comment data to the UI.
    Protects the Domain entity from being exposed directly to the templates.
    Handles formatting of complex types like dates.

    Attributes:
        author_avatar_file_id (str | None): UUID of the author's avatar file, or None.
    """
    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    comment_article_id: int
    comment_written_account_id: int | None
    author_username: str = "Unknown"
    author_avatar_file_id: str | None = None
    comment_reply_to: int | None
    comment_content: str
    comment_posted_at_formatted: str = ""

    @classmethod
    def from_domain(cls, comment, author_username: str = "Unknown", author_avatar_file_id: str | None = None):
        """
        Helper factory to create a response DTO from a domain Comment entity.
        Formats the posting date into a reader-friendly string.

        Args:
            comment (Comment): The domain comment entity.
            author_username (str): The username of the comment author.
                Overridden to "Anonymous" if comment_content is "Comment removed" or "[deleted]".
            author_avatar_file_id (str | None): Optional UUID of the author's avatar file.

        Returns:
            CommentResponse: The initialized DTO.
        """
        content = comment.comment_content

        if comment.comment_written_account_id is None:
            author_username = "Anonymous"
            content = "<!--cmt-removed--><em>Comment removed</em>"

        if "<!--cmt-removed-->" in content or content in ("Comment removed", "[deleted]"):
            author_username = "Anonymous"

        if "<!--cmt-removed-->" in content:
            content = content.replace("<!--cmt-removed-->", "")

        formatted_date = ""
        if comment.comment_posted_at:
            formatted_date = comment.comment_posted_at.strftime("%B %d, %Y at %H:%M")

        return cls(
            comment_id=comment.comment_id,
            comment_article_id=comment.comment_article_id,
            comment_written_account_id=comment.comment_written_account_id,
            author_username=author_username,
            author_avatar_file_id=author_avatar_file_id,
            comment_reply_to=comment.comment_reply_to,
            comment_content=content,
            comment_posted_at_formatted=formatted_date
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
