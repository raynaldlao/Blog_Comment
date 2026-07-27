import time
from datetime import UTC, datetime

import nh3

from blog_exceptions import (
    AccountBannedError,
    AccountNotFoundError,
    ArticleNotFoundError,
    CommentAuthorizationError,
    CommentDeletedError,
    CommentNotFoundError,
    CommentValidationError,
)
from src.application.domain.account import Account, AccountRole
from src.application.domain.comment import Comment
from src.application.input_ports.comment_management import CommentManagementPort
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.output_ports.comment_repository import CommentRepository


class CommentService(CommentManagementPort):
    """
    Implements the CommentManagementPort input port.
    Handles all business logic operations related to Comments.
    Depends on CommentRepository, ArticleRepository, and AccountRepository output ports
    for data persistence, injected via the constructor.
    """

    MAX_REPLY_DEPTH = 3
    COMMENT_INTERVAL = 1

    ALLOWED_TAGS = frozenset({
        "b", "i", "u", "s", "strike", "del", "a", "ul", "ol", "li", "br", "p", "em", "strong",
        "blockquote", "pre", "code", "span", "sub", "sup",
    })

    def __init__(
        self,
        comment_repository: CommentRepository,
        article_repository: ArticleRepository,
        account_repository: AccountRepository,
    ):
        self.comment_repository = comment_repository
        self.article_repository = article_repository
        self.account_repository = account_repository
        self._user_comment_timestamps: dict[int, float] = {}

    def _get_account_if_exists(self, user_id: int) -> Account:
        """
        Retrieves an account by user ID.

        Args:
            user_id (int): The ID of the user to look up.

        Returns:
            Account: The Account domain entity.

        Raises:
            AccountNotFoundError: If the account does not exist.
            AccountBannedError: If the account is banned.
        """
        account = self.account_repository.get_by_id(user_id)
        if not account:
            raise AccountNotFoundError("Compte introuvable.")
        if account.is_banned:
            raise AccountBannedError("Le compte est banni.")
        return account

    @staticmethod
    def _get_comment_depth(comment_id: int, comment_repo: CommentRepository) -> int:
        depth = 0
        current_id = comment_id
        for _ in range(10):
            parent = comment_repo.get_by_id(current_id)
            if not parent or parent.comment_reply_to is None:
                break
            current_id = parent.comment_reply_to
            depth += 1
        return depth


    def check_rate_limit(self, user_id: int) -> int | None:
        """
        Checks if the user is posting comments too fast based on COMMENT_INTERVAL class constant.

        Maintains an in-memory timestamp dict per user. Returns remaining cooldown
        seconds if the user has posted within the interval, or None to allow the post.

        Args:
            user_id (int): ID of the user to check.

        Returns:
            int | None: Remaining cooldown seconds, or None if the user can post.
        """
        now = time.time()
        last = self._user_comment_timestamps.get(user_id)
        if last:
            elapsed = now - last
            if elapsed < self.COMMENT_INTERVAL:
                return max(1, int(self.COMMENT_INTERVAL - elapsed))
        self._user_comment_timestamps[user_id] = now
        return None

    def create_comment(self, article_id: int, user_id: int, content: str) -> Comment:
        """
        Creates a new top-level comment on an article.

        Validates the account, checks article existence, sanitizes HTML content,
        and persists the comment.

        Args:
            article_id (int): ID of the article to comment on.
            user_id (int): ID of the author account.
            content (str): Raw comment text (may contain limited HTML).

        Returns:
            Comment: The created Comment domain entity.

        Raises:
            AccountNotFoundError: If the account does not exist.
            AccountBannedError: If the account is banned.
            ArticleNotFoundError: If the article does not exist.
            CommentValidationError: If the content is empty after sanitization.
        """
        account = self._get_account_if_exists(user_id)

        article = self.article_repository.get_by_id(article_id)
        if not article:
            raise ArticleNotFoundError("Article introuvable.")

        sanitized = nh3.clean(
            content,
            tags=self.ALLOWED_TAGS,
            attributes={"a": {"href", "target"}},
            link_rel="noopener noreferrer",
        )
        if not sanitized.strip():
            raise CommentValidationError("Le commentaire ne peut pas être vide.")
        fake_comment_id = 0
        new_comment = Comment(
            comment_id=fake_comment_id,
            comment_article_id=article.article_id,
            comment_written_account_id=account.account_id,
            comment_reply_to=None,
            comment_content=sanitized,
            comment_posted_at=datetime.now(UTC),
        )

        self.comment_repository.save(new_comment)
        return new_comment

    def create_reply(self, parent_comment_id: int, user_id: int, content: str) -> Comment:
        """
        Creates a reply to an existing comment.

        Validates parent comment exists, is not deleted, and respects max nesting depth.

        Args:
            parent_comment_id (int): ID of the parent comment to reply to.
            user_id (int): ID of the author account.
            content (str): Raw reply text (may contain limited HTML).

        Returns:
            Comment: The created Comment domain entity.

        Raises:
            AccountNotFoundError: If the account does not exist.
            AccountBannedError: If the account is banned.
            CommentNotFoundError: If the parent comment does not exist.
            CommentDeletedError: If the parent comment is deleted.
            CommentValidationError: If the content is empty or max depth exceeded.
        """
        account = self._get_account_if_exists(user_id)

        parent_comment = self.comment_repository.get_by_id(parent_comment_id)
        if not parent_comment:
            raise CommentNotFoundError("Commentaire parent introuvable.")

        if parent_comment.is_deleted:
            raise CommentDeletedError("Impossible de répondre à un commentaire supprimé.")

        parent_depth = self._get_comment_depth(parent_comment.comment_id, self.comment_repository)
        if parent_depth >= self.MAX_REPLY_DEPTH:
            raise CommentValidationError("Impossible de répondre à un commentaire ayant atteint la profondeur maximale.")

        sanitized = nh3.clean(
            content,
            tags=self.ALLOWED_TAGS,
            attributes={"a": {"href", "target"}},
            link_rel="noopener noreferrer",
        )
        if not sanitized.strip():
            raise CommentValidationError("Le commentaire ne peut pas être vide.")
        fake_comment_id = 0
        new_reply = Comment(
            comment_id=fake_comment_id,
            comment_article_id=parent_comment.comment_article_id,
            comment_written_account_id=account.account_id,
            comment_content=sanitized,
            comment_reply_to=parent_comment.comment_id,
            comment_posted_at=datetime.now(UTC),
        )

        self.comment_repository.save(new_reply)
        return new_reply

    def mask_comments_by_account_id(self, account_id: int) -> None:
        """
        Masks all comments by a given account (used during account deletion).

        Sets is_deleted=True, deleted_at=now, and replaces content with a removal notice.

        Args:
            account_id (int): ID of the account whose comments should be masked.
        """
        comments = self.comment_repository.get_by_account_id(account_id)
        for comment in comments:
            comment.comment_content = "<!--cmt-removed--><em>Comment removed</em>"
            comment.is_deleted = True
            comment.deleted_at = datetime.now(UTC)
            comment.deleted_by = "account_deleted"
            self.comment_repository.save(comment)

    def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """
        Soft-deletes a comment. Author or admin only. Idempotent if already deleted.

        Args:
            comment_id (int): ID of the comment to delete.
            user_id (int): ID of the requesting user.

        Returns:
            bool: True on success.

        Raises:
            AccountNotFoundError: If the account does not exist.
            AccountBannedError: If the account is banned.
            CommentNotFoundError: If the comment does not exist.
            CommentAuthorizationError: If the user is not the author nor admin.
        """
        account = self._get_account_if_exists(user_id)
        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFoundError("Commentaire introuvable.")

        is_author = comment.comment_written_account_id == account.account_id
        is_admin = account.account_role == AccountRole.ADMIN
        if not is_author and not is_admin:
            raise CommentAuthorizationError("Non autorisé : vous ne pouvez supprimer que vos propres commentaires.")

        if comment.is_deleted:
            return True

        comment.is_deleted = True
        comment.deleted_at = datetime.now(UTC)
        comment.deleted_by = "admin" if is_admin and not is_author else "user"
        self.comment_repository.save(comment)
        return True

    def edit_comment(self, comment_id: int, user_id: int, content: str) -> Comment:
        """
        Edits a comment's content. Author only (not admin). Cannot edit a deleted comment.

        Args:
            comment_id (int): ID of the comment to edit.
            user_id (int): ID of the requesting user (must be the author).
            content (str): New comment text (may contain limited HTML).

        Returns:
            Comment: The updated Comment domain entity.

        Raises:
            AccountNotFoundError: If the account does not exist.
            AccountBannedError: If the account is banned.
            CommentNotFoundError: If the comment does not exist.
            CommentAuthorizationError: If the user is not the comment author.
            CommentDeletedError: If the comment has been deleted.
            CommentValidationError: If the content is empty after sanitization.
        """
        account = self._get_account_if_exists(user_id)
        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFoundError("Commentaire introuvable.")

        if comment.comment_written_account_id != account.account_id:
            raise CommentAuthorizationError("Non autorisé : vous ne pouvez modifier que vos propres commentaires.")

        if comment.is_deleted:
            raise CommentDeletedError("Impossible de modifier un commentaire supprimé.")

        sanitized = nh3.clean(
            content,
            tags=self.ALLOWED_TAGS,
            attributes={"a": {"href", "target"}},
            link_rel="noopener noreferrer",
        )
        if not sanitized.strip():
            raise CommentValidationError("Le commentaire ne peut pas être vide.")

        comment.comment_content = sanitized
        comment.edited_at = datetime.now(UTC)
        self.comment_repository.save(comment)
        return comment

    def hard_delete_comment(self, comment_id: int, user_id: int) -> bool:
        """
        Permanently deletes a comment from the database. Admin only.
        Only allowed on already soft-deleted comments.
        Children are automatically deleted via FK ON DELETE CASCADE.

        Args:
            comment_id (int): ID of the comment to permanently delete.
            user_id (int): ID of the requesting user (must be admin).

        Returns:
            bool: True on success.

        Raises:
            AccountNotFoundError: If the account does not exist.
            AccountBannedError: If the account is banned.
            CommentNotFoundError: If the comment does not exist.
            CommentAuthorizationError: If the user is not an admin.
            CommentValidationError: If the comment is not soft-deleted first.
        """
        account = self._get_account_if_exists(user_id)
        if account.account_role != AccountRole.ADMIN:
            raise CommentAuthorizationError(
                "Non autorisé : seuls les administrateurs peuvent supprimer définitivement des commentaires."
            )

        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFoundError("Commentaire introuvable.")

        if not comment.is_deleted:
            raise CommentValidationError("Le commentaire n'est pas supprimé. Supprimez-le d'abord avec la suppression standard.")

        self.comment_repository.delete(comment_id)
        return True
