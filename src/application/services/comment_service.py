from datetime import datetime

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
        """
        Initialize the service via Dependency Injection.

        Args:
            comment_repository (CommentRepository): Port for comment data access.
            article_repository (ArticleRepository): Port for article data access.
            account_repository (AccountRepository): Port for account data access.
        """
        self.comment_repository = comment_repository
        self.article_repository = article_repository
        self.account_repository = account_repository

    def _get_account_if_exists(self, user_id: int) -> Account | str:
        """
        Helper method to retrieve and validate an account.

        Args:
            user_id (int): The unique identifier of the user to check.

        Returns:
            Account | str: The Account domain entity if found, or an error message string.
        """
        account = self.account_repository.get_by_id(user_id)
        if not account:
            # TODO: Raise AccountNotFoundException
            return "Account not found."
        return account

    @staticmethod
    def _get_comment_depth(comment_id: int, comment_repo: CommentRepository) -> int:
        """
        Walks comment_reply_to chain up to root to compute nesting depth.

        Args:
            comment_id (int): ID of the comment to measure depth for.
            comment_repo (CommentRepository): Repository for loading comments.

        Returns:
            int: Nesting depth (0 for root comment).
        """
        depth = 0
        current_id = comment_id
        for _ in range(10):
            parent = comment_repo.get_by_id(current_id)
            if not parent or parent.comment_reply_to is None:
                break
            current_id = parent.comment_reply_to
            depth += 1
        return depth

    def _delete_with_descendants(self, comment_id: int) -> None:
        """
        Recursively deletes a comment and all its descendants from the repository.

        Traverses the reply tree depth-first, deleting leaf comments first
        to respect foreign key constraints.

        Args:
            comment_id (int): ID of the root comment to delete along with its subtree.
        """
        children = self.comment_repository.get_by_reply_to(comment_id)
        for child in children:
            self._delete_with_descendants(child.comment_id)
        self.comment_repository.delete(comment_id)


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
        account_or_error = self._get_account_if_exists(user_id)
        if isinstance(account_or_error, str):
            # TODO: Raise UnauthorizedException later
            return account_or_error

        account: Account = account_or_error

        article = self.article_repository.get_by_id(article_id)
        if not article:
            # TODO: Raise ArticleNotFoundException later
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
            comment_posted_at=datetime.now(),
        )

        self.comment_repository.save(new_comment)
        return new_comment

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
        account_or_error = self._get_account_if_exists(user_id)
        if isinstance(account_or_error, str):
            # TODO: Raise UnauthorizedException later
            return account_or_error

        account: Account = account_or_error

        parent_comment = self.comment_repository.get_by_id(parent_comment_id)
        if not parent_comment:
            # TODO: Raise CommentNotFoundException later
            return "Parent comment not found."

        if "<!--cmt-removed-->" in parent_comment.comment_content:
            # TODO: Raise CannotReplyException later
            return "Cannot reply to a removed comment."

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
            comment_posted_at=datetime.now(),
        )

        self.comment_repository.save(new_reply)
        return new_reply

    def get_comments_for_article(self, article_id: int) -> list[CommentNode] | str:
        """
        Retrieves all comments for a specific article and structures them
        in a nested tree for display, along with author names.

        Args:
            article_id (int): ID of the article.

        Returns:
            list[CommentNode] | str: The nested tree root nodes,
            or an error message string if the article is not found.
        """
        article = self.article_repository.get_by_id(article_id)
        if not article:
            # TODO: Raise ArticleNotFoundException later
            return "Article not found."

        all_comments = self.comment_repository.get_all_by_article_id(article_id)
        author_ids = {c.comment_written_account_id for c in all_comments if c.comment_written_account_id is not None}
        authors = self.account_repository.get_by_ids(list(author_ids))
        author_map = {acc.account_id: acc.account_username for acc in authors}
        avatar_map = {acc.account_id: acc.avatar_file_id for acc in authors}
        return build_comment_nested_tree(all_comments, author_map, avatar_map)

    def delete_comment(self, comment_id: int, user_id: int) -> bool | str:
        """
        Deletes a comment. First click soft-deletes (content → "Comment removed", author → Anonymous).
        Second click hard-deletes: removes the comment and all its descendants recursively.

        Args:
            comment_id (int): ID of the comment to delete.
            user_id (int): ID of the user requesting the deletion.

        Returns:
            bool | str: True if deletion was successful, or an error message string.
        """
        account_or_error = self._get_account_if_exists(user_id)
        if isinstance(account_or_error, str):
            # TODO: Raise UnauthorizedException later
            return account_or_error

        account: Account = account_or_error

        if account.account_role != AccountRole.ADMIN:
            # TODO: Raise InsufficientPermissionsException later
            return "Unauthorized : Only admins can delete comments."

        comment = self.comment_repository.get_by_id(comment_id)
        if not comment:
            # TODO: Raise CommentNotFoundException later
            return "Comment not found."

        if "<!--cmt-removed-->" in comment.comment_content:
            self._delete_with_descendants(comment_id)
            return True

        comment.comment_content = "<!--cmt-removed--><em>Comment removed</em>"
        self.comment_repository.save(comment)
        return True
