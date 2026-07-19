from src.application.domain.comment import Comment
from src.application.output_ports.comment_repository import CommentRepository


class InMemoryCommentRepository(CommentRepository):
    """
    In-memory implementation of the CommentRepository.
    Uses a dictionary to store comments, intended for unit tests and rapid prototyping.
    """

    def __init__(self):
        """
        Initializes the repository with an empty internal dictionary and ID counter.
        """
        self._comments: dict[int, Comment] = {}
        self._next_id = 1

    def save(self, comment: Comment) -> None:
        """
        Saves a new comment or updates an existing one. If the comment_id is 0,
        an auto-incremented ID will be assigned.

        Args:
            comment (Comment): The Comment domain entity to save.
        """
        if comment.comment_id == 0:
            comment.comment_id = self._next_id
            self._next_id += 1
        self._comments[comment.comment_id] = comment

    def get_by_id(self, comment_id: int) -> Comment | None:
        """
        Retrieves a single comment by ID.

        Args:
            comment_id (int): The unique identifier.

        Returns:
            Comment | None: The domain Comment or None if missing.
        """
        return self._comments.get(comment_id)

    def get_all_by_article_id(self, article_id: int) -> list[Comment]:
        """
        Retrieves all comments associated with a specific article.

        Args:
            article_id (int): ID of the article.

        Returns:
            list[Comment]: A list of all Comment domain entities for this article.
        """
        return [c for c in self._comments.values() if c.comment_article_id == article_id]

    def get_by_reply_to(self, comment_id: int) -> list[Comment]:
        """
        Retrieves all direct child comments that reply to a given comment.

        Args:
            comment_id (int): ID of the parent comment.

        Returns:
            list[Comment]: A list of direct child Comment domain entities.
        """
        return [c for c in self._comments.values() if c.comment_reply_to == comment_id]

    def get_by_account_id(self, account_id: int) -> list[Comment]:
        """
        Retrieves all comments authored by a specific account.

        Args:
            account_id (int): ID of the account.

        Returns:
            list[Comment]: A list of Comment domain entities for this author.
        """
        return [
            c for c in self._comments.values()
            if c.comment_written_account_id == account_id
        ]

    def delete(self, comment_id: int) -> None:
        """
        Deletes a comment by its ID.

        Args:
            comment_id (int): ID of the comment to remove.
        """
        if comment_id in self._comments:
            del self._comments[comment_id]
