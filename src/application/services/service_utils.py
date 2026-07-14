from collections import defaultdict

from src.application.domain.comment import Comment, CommentNode, CommentWithAuthor


def build_comment_nested_tree(all_comments: list[Comment], author_map: dict[int, str]) -> list[CommentNode]:
    """
    Transforms a flat list of comment entities and an author mapping into a recursive N-level tree.

    Builds a parent_map from comment_reply_to, then recurses from roots (reply_to is None)
    to produce a nested CommentNode tree with sorted children.

    Args:
        all_comments (list[Comment]): The flat list of domain comment entities to structure.
        author_map (dict[int, str]): A mapping of account IDs to their corresponding usernames.

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
            author_name=author_map.get(comment.comment_written_account_id, "Unknown")
        )
        children = parent_map.pop(comment.comment_id, [])
        children.sort(key=lambda c: c.comment_posted_at)
        replies = [_build_node(child, depth + 1) for child in children]
        return CommentNode(comment=cwa, replies=replies, depth=depth)

    return [_build_node(root, 0) for root in roots]
