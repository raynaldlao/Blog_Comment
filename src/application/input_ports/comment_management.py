from abc import ABC, abstractmethod

from src.application.domain.comment import Comment


class CommentManagementPort(ABC):
    """
    Input port (interface) defining the business operations for comment management.
    This serves as the API of the Core, to be used by input adapters (Web, CLI, etc.).
    """

    @abstractmethod
    def create_comment(self, article_id: int, user_id: int, content: str) -> Comment | str:
        """
        Creates a top-level comment on an article.

        Args:
            article_id (int): ID of the article being commented on.
            user_id (int): ID of the user creating the comment.
            content (str): Text content of the comment.

        Returns:
            Comment | str: The created Comment entity, or an error message string.
        """
        pass

    @abstractmethod
    def create_reply(self, parent_comment_id: int, user_id: int, content: str) -> Comment | str:
        """
        Creates a reply to an existing comment.
        A reply is linked to the thread's top-level comment (threading logic).

        Args:
            parent_comment_id (int): The ID of the comment being replied to.
            user_id (int): The identifier of the user creating the reply.
            content (str): The text content of the reply.

        Returns:
            Comment | str: The new Comment domain entity if successful,
            or an error message string if unauthorized or parent not found.
        """
        pass

    @abstractmethod
    def get_comments_for_article(self, article_id: int) -> dict[str | int, list[Comment]] | str:
        """
        Retrieves all comments for a specific article and structures them
        into a threaded dictionary for display.

        Args:
            article_id (int): ID of the article.

        Returns:
            dict[str | int, list[Comment]] | str: A dictionary containing the threaded comments,
            or an error message string if the article is not found.
            Structure:
            {
                "root": [Comment1, Comment2],
                comment_id_1: [Reply1, Reply2],
                comment_id_2: [Reply3]
            }
        """
        pass

    @abstractmethod
    def delete_comment(self, comment_id: int, user_id: int) -> bool | str:
        """
        Deletes a comment. Only an admin can delete a comment.

        Args:
            comment_id (int): ID of the comment to delete.
            user_id (int): ID of the user requesting the deletion.

        Returns:
            bool | str: True if deletion was successful, or an error message string.
        """
        pass
