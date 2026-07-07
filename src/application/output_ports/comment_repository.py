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
    def get_by_reply_to(self, comment_id: int) -> list[Comment]:
        """
        Retrieves all direct child comments that reply to a given comment.

        Args:
            comment_id (int): ID of the parent comment.

        Returns:
            list[Comment]: A list of direct child Comment domain entities.
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
