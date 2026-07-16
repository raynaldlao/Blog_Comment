from collections import defaultdict

from src.application.domain.comment import Comment, CommentNode, CommentWithAuthor


def build_comment_nested_tree(
    all_comments: list[Comment],
    author_map: dict[int, str],
    avatar_map: dict[int, str | None] | None = None,
) -> list[CommentNode]:
    """
    Transforms a flat list of comment entities and author/avatar mappings into a recursive N-level tree.

    Builds a parent_map from comment_reply_to, then recurses from roots (reply_to is None)
    to produce a nested CommentNode tree with sorted children.

    Args:
        all_comments (list[Comment]): The flat list of domain comment entities to structure.
        author_map (dict[int, str]): A mapping of account IDs to their usernames.
        avatar_map (dict[int, str | None] | None): Optional mapping of account IDs
            to their avatar file IDs. Defaults to None.

    Returns:
        list[CommentNode]: The tree root nodes, sorted most recent first.
    """
    parent_map: dict[int | None, list[Comment]] = defaultdict(list)
    for c in all_comments:
        parent_map[c.comment_reply_to].append(c)

    roots = parent_map.pop(None, [])
    roots.sort(key=lambda c: c.comment_posted_at, reverse=True)

    def _build_node(comment: Comment, depth: int) -> CommentNode:
        cwa = CommentWithAuthor(
            comment=comment,
            author_name=author_map.get(comment.comment_written_account_id, "Unknown"),
            author_avatar_file_id=(
                avatar_map.get(comment.comment_written_account_id)
                if avatar_map else None
            ),
        )
        children = parent_map.pop(comment.comment_id, [])
        children.sort(key=lambda c: c.comment_posted_at)
        replies = [_build_node(child, depth + 1) for child in children]
        return CommentNode(comment=cwa, replies=replies, depth=depth)

    return [_build_node(root, 0) for root in roots]
