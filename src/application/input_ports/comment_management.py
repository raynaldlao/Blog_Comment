from abc import ABC, abstractmethod

from src.application.domain.comment import Comment, CommentNode


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
        Creates a reply directly to a parent comment.

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
    def get_comments_for_article(self, article_id: int) -> list[CommentNode] | str:
        """
        Retrieves all comments for a specific article and structures them
        into a nested tree for display, along with associated author names.

        Args:
            article_id (int): ID of the article.

        Returns:
            list[CommentNode] | str: The nested tree root nodes,
            or an error message string if the article is not found.
        """
        pass

    @abstractmethod
    def mask_comments_by_account_id(self, account_id: int) -> None:
        """
        Masks all comments authored by the given account as removed.
        Sets the comment content to a "Comment removed" marker.

        Called during account deletion to soft-remove the user's comments
        before the account record is deleted.

        Args:
            account_id (int): ID of the account whose comments to mask.
        """
        pass

    @abstractmethod
    def delete_comment(self, comment_id: int, user_id: int) -> bool | str:
        """
        Soft-deletes a comment.
        Sets is_deleted=True and deleted_at=now.
        Author and admin can soft-delete.
        Content preserved in DB but display shows "Comment removed".
        Author displayed as "Anonymous" after deletion.

        Args:
            comment_id (int): ID of the comment to delete.
            user_id (int): ID of the user requesting the deletion.

        Returns:
            bool | str: True if deletion was successful, or an error message string.
        """
        pass

    @abstractmethod
    def edit_comment(self, comment_id: int, user_id: int, content: str) -> Comment | str:
        """
        Edits a comment's content.
        Author only (not admin).
        Updates content and sets edited_at=now.
        Cannot edit a deleted comment.

        Args:
            comment_id (int): ID of the comment to edit.
            user_id (int): ID of the user requesting the edit.
            content (str): New text content of the comment.

        Returns:
            Comment | str: The updated Comment entity, or an error message string.
        """
        pass

    @abstractmethod
    def hard_delete_comment(self, comment_id: int, user_id: int) -> bool | str:
        """
        Permanently deletes a comment from the database. Admin only.
        Intended for removing already soft-deleted comments.
        Children comments get comment_reply_to set to NULL via FK.

        Args:
            comment_id (int): ID of the comment to permanently delete.
            user_id (int): ID of the requesting user (must be admin).

        Returns:
            bool | str: True if deletion was successful, or an error message string.
        """
        pass
