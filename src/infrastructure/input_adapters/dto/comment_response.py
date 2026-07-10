from __future__ import annotations

from dataclasses import dataclass, field

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
                Overridden to "Anonymous" if comment_content is "Comment removed" or "[deleted]".

        Returns:
            CommentResponse: The initialized DTO.
        """
        content = comment.comment_content
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
            comment_reply_to=comment.comment_reply_to,
            comment_content=content,
            comment_posted_at_formatted=formatted_date
        )

    @classmethod
    def map_nested_tree(cls, nodes: list, depth_limit: int = 4) -> list[CommentNodeResponse]:
        """
        Recursively maps a list of CommentNode domain tree nodes into DTO tree nodes.

        Args:
            nodes (list[CommentNode]): The root tree nodes from the domain layer.
            depth_limit (int): Maximum rendering depth; deeper nodes are flattened.

        Returns:
            list[CommentNodeResponse]: The mapped DTO tree.
        """
        def _map(node) -> CommentNodeResponse:
            display_depth = node.depth if node.depth < depth_limit else depth_limit
            cr = cls.from_domain(node.comment.comment, node.comment.author_name)
            replies = [_map(child) for child in node.replies]
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
