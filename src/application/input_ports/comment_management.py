from abc import ABC, abstractmethod

from src.application.domain.comment import Comment, CommentNode


class CommentManagementPort(ABC):
    """
    Input port (interface) defining the business operations for comment management.
    This serves as the API of the Core, to be used by input adapters (Web, CLI, etc.).
    """

    @abstractmethod
    def create_comment(self, article_id: int, user_id: int, content: str) -> Comment:
        """
        Creates a top-level comment on an article.

        Args:
            article_id (int): ID of the article being commented on.
            user_id (int): ID of the user creating the comment.
            content (str): Text content of the comment.

        Returns:
            Comment: The created Comment entity.

        Raises:
            AccountNotFoundError: If the account is not found.
            AccountBannedError: If the account is banned.
            ArticleNotFoundError: If the article does not exist.
            CommentValidationError: If the content is empty after sanitization.
        """
        pass

    @abstractmethod
    def create_reply(self, parent_comment_id: int, user_id: int, content: str) -> Comment:
        """
        Creates a reply directly to a parent comment.

        Args:
            parent_comment_id (int): The ID of the comment being replied to.
            user_id (int): The identifier of the user creating the reply.
            content (str): The text content of the reply.

        Returns:
            Comment: The new Comment domain entity if successful.

        Raises:
            AccountNotFoundError: If the account is not found.
            AccountBannedError: If the account is banned.
            CommentNotFoundError: If the parent comment does not exist.
            CommentDeletedError: If the parent comment is deleted.
            CommentValidationError: If the content is empty or max depth exceeded.
        """
        pass

    @abstractmethod
    def get_comments_for_article(self, article_id: int) -> list[CommentNode]:
        """
        Retrieves all comments for a specific article and structures them
        into a nested tree for display, along with associated author names.

        Args:
            article_id (int): ID of the article.

        Returns:
            list[CommentNode]: The nested tree root nodes.

        Raises:
            ArticleNotFoundError: If the article does not exist.
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
    def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """
        Soft-deletes a comment.
        Sets is_deleted=True and deleted_at=now.
        Author and admin can soft-delete.
        Content preserved in DB but display shows "Comment removed".

        Args:
            comment_id (int): ID of the comment to delete.
            user_id (int): ID of the user requesting the deletion.

        Returns:
            bool: True if deletion was successful.

        Raises:
            AccountNotFoundError: If the account is not found.
            AccountBannedError: If the account is banned.
            CommentNotFoundError: If the comment does not exist.
            CommentAuthorizationError: If the user is not the author nor admin.
        """
        pass

    @abstractmethod
    def edit_comment(self, comment_id: int, user_id: int, content: str) -> Comment:
        """
        Edits a comment's content. Author only (not admin).
        Updates content and sets edited_at=now. Cannot edit a deleted comment.

        Args:
            comment_id (int): ID of the comment to edit.
            user_id (int): ID of the user requesting the edit.
            content (str): New text content of the comment.

        Returns:
            Comment: The updated Comment entity.

        Raises:
            AccountNotFoundError: If the account is not found.
            AccountBannedError: If the account is banned.
            CommentNotFoundError: If the comment does not exist.
            CommentAuthorizationError: If the user is not the comment author.
            CommentDeletedError: If the comment has been deleted.
            CommentValidationError: If the content is empty after sanitization.
        """
        pass

    @abstractmethod
    def check_rate_limit(self, user_id: int) -> int | None:
        """
        Checks if the user is posting comments too fast based on a configurable interval.

        Args:
            user_id (int): ID of the user to check.

        Returns:
            int | None: Number of remaining cooldown seconds if rate-limited, or None if allowed.
        """
        pass

    @abstractmethod
    def hard_delete_comment(self, comment_id: int, user_id: int) -> bool:
        """
        Permanently deletes a comment from the database. Admin only.
        Only allowed on already soft-deleted comments.

        Args:
            comment_id (int): ID of the comment to permanently delete.
            user_id (int): ID of the requesting user (must be admin).

        Returns:
            bool: True if deletion was successful.

        Raises:
            AccountNotFoundError: If the account is not found.
            AccountBannedError: If the account is banned.
            CommentNotFoundError: If the comment does not exist.
            CommentAuthorizationError: If the user is not an admin.
            CommentValidationError: If the comment is not soft-deleted first.
        """
        pass
