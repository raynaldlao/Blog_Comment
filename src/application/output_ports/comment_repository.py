from abc import ABC, abstractmethod

from src.application.domain.comment import Comment


class CommentRepository(ABC):
    """
    Output port (interface) for Comment persistence operations.
    Defines how the application interacts with the database for comments.
    """

    @abstractmethod
    def save(self, comment: Comment) -> None:
        """
        Saves a new comment or updates an existing one.

        Args:
            comment (Comment): The Comment domain entity to save.
        """
        pass

    @abstractmethod
    def get_by_id(self, comment_id: int) -> Comment | None:
        """
        Retrieves a single comment by its ID.

        Args:
            comment_id (int): The unique identifier of the comment.

        Returns:
            Comment | None: The Comment domain entity if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_all_by_article_id(self, article_id: int) -> list[Comment]:
        """
        Retrieves all comments associated with a specific article.

        Args:
            article_id (int): ID of the article.

        Returns:
            list[Comment]: A list of all Comment domain entities for this article.
        """
        pass

    @abstractmethod
    def get_by_account_id(self, account_id: int) -> list[Comment]:
        """
        Retrieves all comments authored by a specific account.

        Args:
            account_id (int): ID of the account.

        Returns:
            list[Comment]: A list of Comment domain entities for this author.
        """
        pass

    @abstractmethod
    def get_last_comment_timestamp(self, user_id: int) -> float | None:
        """Retrieves the Unix timestamp of the most recent comment by a user.

        Args:
            user_id: ID of the user to query.

        Returns:
            Unix timestamp (seconds since epoch) of the latest comment,
            or None if the user has no comments.
        """
        pass

    @abstractmethod
    def mask_comments_by_account_id(self, account_id: int) -> None:
        """Sets is_deleted=True, masks content, and sets deleted_at/deleted_by
        for all comments by the given account.

        Args:
            account_id: ID of the account whose comments should be masked.
        """
        pass

    @abstractmethod
    def delete(self, comment_id: int) -> None:
        """
        Deletes a comment by its ID from the repository.

        Args:
            comment_id (int): ID of the comment to remove.
        """
        pass
