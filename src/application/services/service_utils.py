from datetime import datetime
from collections import defaultdict

from src.application.domain.comment import Comment, CommentThreadView, CommentWithAuthor


def _get_posted_at_date(item: CommentWithAuthor) -> datetime:
    """
    Extracts the posting date from a CommentWithAuthor object.
    Used as a key for sorting comments in the threading logic.

    Args:
        item (CommentWithAuthor): The comment wrapper object containing domain data.

    Returns:
        datetime: The date and time the comment was posted.
    """
    return item.comment.comment_posted_at


def build_comment_thread_view(all_comments: list[Comment], author_map: dict[int, str]) -> CommentThreadView:
    """
    Transforms a flat list of comment entities and an author mapping into a structured threaded view.
    Handles grouping by parent and sorting by date (descending for root, ascending for replies).

    Args:
        all_comments (list[Comment]): The flat list of domain comment entities to structure.
        author_map (dict[int, str]): A mapping of account IDs to their corresponding usernames.

    Returns:
        CommentThreadView: The structured read model containing the threaded hierarchy.
    """
    tree = defaultdict(list)
    tree["root"] = []

    for comment in all_comments:
        if comment.comment_reply_to is None:
            key = "root"
        else:
            key = comment.comment_reply_to

        comment_with_author = CommentWithAuthor(
            comment=comment,
            author_name=author_map.get(comment.comment_written_account_id, "Unknown")
        )
        tree[key].append(comment_with_author)

    if "root" in tree:
        tree["root"].sort(key=_get_posted_at_date, reverse=True)

    for root_comment in tree["root"]:
        node_id = root_comment.comment.comment_id
        if node_id in tree:
            tree[node_id].sort(key=_get_posted_at_date)

    return CommentThreadView(threads=dict(tree))
