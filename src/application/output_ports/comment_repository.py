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
