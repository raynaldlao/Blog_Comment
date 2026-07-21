from datetime import UTC, datetime

import nh3

from src.application.domain.account import Account, AccountRole
from src.application.domain.comment import Comment, CommentNode
from src.application.input_ports.comment_management import CommentManagementPort
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.output_ports.comment_repository import CommentRepository
from src.application.services.service_utils import build_comment_nested_tree

MAX_REPLY_DEPTH = 3


class CommentService(CommentManagementPort):
    """
    Implements the CommentManagementPort input port.
    Handles all business logic operations related to Comments.
    Depends on CommentRepository, ArticleRepository, and AccountRepository output ports
    for data persistence, injected via the constructor.
    """

    ALLOWED_TAGS = frozenset({
        "b", "i", "u", "s", "a", "ul", "ol", "li", "br", "p", "em", "strong",
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

    def _get_account_if_exists(self, user_id: int) -> Account | str:
        """
        Retrieves an account by user ID. Returns error string if not found or banned.

        Args:
            user_id (int): The ID of the user to look up.

        Returns:
            Account | str: The Account domain entity, or an error message string.
        """
        account = self.account_repository.get_by_id(user_id)
        if not account:
            return "Account not found."
        if account.is_banned:
            return "Account is banned."
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


    def create_comment(self, article_id: int, user_id: int, content: str) -> Comment | str:
        """
        Creates a new top-level comment on an article.

        Validates the account, checks article existence, sanitizes HTML content,
        and persists the comment.

        Args:
            article_id (int): ID of the article to comment on.
            user_id (int): ID of the author account.
            content (str): Raw comment text (may contain limited HTML).

        Returns:
            Comment | str: The created Comment domain entity, or an error message.
        """
        account_or_error = self._get_account_if_exists(user_id)
        if isinstance(account_or_error, str):
            return account_or_error

        account: Account = account_or_error

        article = self.article_repository.get_by_id(article_id)
        if not article:
            return "Article not found."

        sanitized = nh3.clean(
            content,
            tags=self.ALLOWED_TAGS,
            attributes={"a": {"href", "target"}},
            link_rel="noopener noreferrer",
        )
        if not sanitized.strip():
            return "Comment cannot be empty."
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

    def create_reply(self, parent_comment_id: int, user_id: int, content: str) -> Comment | str:
        """
        Creates a reply to an existing comment.

        Validates parent comment exists, is not deleted, and respects max nesting depth.

        Args:
            parent_comment_id (int): ID of the parent comment to reply to.
            user_id (int): ID of the author account.
            content (str): Raw reply text (may contain limited HTML).

        Returns:
            Comment | str: The created Comment domain entity, or an error message.
        """
        account_or_error = self._get_account_if_exists(user_id)
        if isinstance(account_or_error, str):
            return account_or_error

        account: Account = account_or_error

        parent_comment = self.comment_repository.get_by_id(parent_comment_id)
        if not parent_comment:
            return "Parent comment not found."

        if parent_comment.is_deleted:
            return "Cannot reply to a deleted comment."

        parent_depth = self._get_comment_depth(parent_comment.comment_id, self.comment_repository)
        if parent_depth >= MAX_REPLY_DEPTH:
            return "Cannot reply to a comment at maximum nesting depth."

        sanitized = nh3.clean(
            content,
            tags=self.ALLOWED_TAGS,
            attributes={"a": {"href", "target"}},
            link_rel="noopener noreferrer",
        )
        if not sanitized.strip():
            return "Comment cannot be empty."
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

    def get_comments_for_article(self, article_id: int) -> list[CommentNode] | str:
        """
        Retrieves all comments for an article as a nested tree.

        Args:
            article_id (int): ID of the article.

        Returns:
            list[CommentNode] | str: List of root CommentNode objects with nested replies,
                or an error message if the article is not found.
        """
        article = self.article_repository.get_by_id(article_id)
        if not article:
            return "Article not found."

        all_comments = self.comment_repository.get_all_by_article_id(article_id)
        author_ids = {c.comment_written_account_id for c in all_comments if c.comment_written_account_id is not None}
        authors = self.account_repository.get_by_ids(list(author_ids))
        author_map = {acc.account_id: acc.account_username for acc in authors}
        avatar_map = {acc.account_id: acc.avatar_file_id for acc in authors}
        return build_comment_nested_tree(all_comments, author_map, avatar_map)

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
            self.comment_repository.save(comment)

    def delete_comment(self, comment_id: int, user_id: int) -> bool | str:
        """
        Soft-deletes a comment. Author or admin only. Idempotent if already deleted.

        Args:
            comment_id (int): ID of the comment to delete.
            user_id (int): ID of the requesting user.

        Returns:
            bool | str: True on success, or an error message string.
        """
        account_or_error = self._get_account_if_exists(user_id)
        if isinstance(account_or_error, str):
            return account_or_error

        account: Account = account_or_error
        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            return "Comment not found."

        is_author = comment.comment_written_account_id == account.account_id
        is_admin = account.account_role == AccountRole.ADMIN
        if not is_author and not is_admin:
            return "Unauthorized: You can only delete your own comments."

        if comment.is_deleted:
            return True

        comment.is_deleted = True
        comment.deleted_at = datetime.now(UTC)
        self.comment_repository.save(comment)
        return True

    def edit_comment(self, comment_id: int, user_id: int, content: str) -> Comment | str:
        """
        Edits a comment's content. Author only (not admin). Cannot edit a deleted comment.

        Args:
            comment_id (int): ID of the comment to edit.
            user_id (int): ID of the requesting user (must be the author).
            content (str): New comment text (may contain limited HTML).

        Returns:
            Comment | str: The updated Comment domain entity, or an error message.
        """
        account_or_error = self._get_account_if_exists(user_id)
        if isinstance(account_or_error, str):
            return account_or_error

        account: Account = account_or_error
        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            return "Comment not found."

        if comment.comment_written_account_id != account.account_id:
            return "Unauthorized: You can only edit your own comments."

        if comment.is_deleted:
            return "Cannot edit a deleted comment."

        sanitized = nh3.clean(
            content,
            tags=self.ALLOWED_TAGS,
            attributes={"a": {"href", "target"}},
            link_rel="noopener noreferrer",
        )
        if not sanitized.strip():
            return "Comment cannot be empty."

        comment.comment_content = sanitized
        comment.edited_at = datetime.now(UTC)
        self.comment_repository.save(comment)
        return comment

    def hard_delete_comment(self, comment_id: int, user_id: int) -> bool | str:
        """
        Permanently deletes a comment from the database. Admin only.
        Only allowed on already soft-deleted comments.
        Children get comment_reply_to set to NULL via FK ON DELETE SET NULL.

        Args:
            comment_id (int): ID of the comment to permanently delete.
            user_id (int): ID of the requesting user (must be admin).

        Returns:
            bool | str: True on success, or an error message string.
        """
        account_or_error = self._get_account_if_exists(user_id)
        if isinstance(account_or_error, str):
            return account_or_error

        account: Account = account_or_error
        if account.account_role != AccountRole.ADMIN:
            return "Unauthorized: Only admins can permanently delete comments."

        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            return "Comment not found."

        if not comment.is_deleted:
            return "Comment is not soft-deleted. Use soft-delete first."

        self.comment_repository.delete(comment_id)
        return True
