from collections import defaultdict
from datetime import datetime
from operator import attrgetter

from src.application.domain.account import Account, AccountRole
from src.application.domain.comment import Comment
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.output_ports.comment_repository import CommentRepository


class CommentService:
    """
    Service responsible for business logic operations related to Comments.
    Depends on CommentRepository, ArticleRepository, and AccountRepository output ports.
    """

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

        fake_comment_id = 0
        new_comment = Comment(
            comment_id=fake_comment_id,
            comment_article_id=article.article_id,
            comment_written_account_id=account.account_id,
            comment_reply_to=None,
            comment_content=content,
            comment_posted_at=datetime.now(),
        )

        self.comment_repository.save(new_comment)
        return new_comment

    def create_reply(self, parent_comment_id: int, user_id: int, content: str) -> Comment | str:
        """
        Creates a reply to an existing comment. A reply is linked
        either to the parent directly or to the parent's top-level
        comment (threading logic).

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

        is_parent_a_reply = parent_comment.comment_reply_to is not None
        if is_parent_a_reply:
            thread_root_id = parent_comment.comment_reply_to
        else:
            thread_root_id = parent_comment.comment_id

        fake_comment_id = 0
        new_reply = Comment(
            comment_id=fake_comment_id,
            comment_article_id=parent_comment.comment_article_id,
            comment_written_account_id=account.account_id,
            comment_content=content,
            comment_reply_to=thread_root_id,
            comment_posted_at=datetime.now(),
        )

        self.comment_repository.save(new_reply)
        return new_reply

    def get_comments_for_article(self, article_id: int) -> dict[str | int, list[Comment]] | str:
        """
        Retrieves all comments for a specific article and structures them
        in a dictionary for easy display (threading).

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
        article = self.article_repository.get_by_id(article_id)
        if not article:
            # TODO: Raise ArticleNotFoundException later
            return "Article not found."

        all_comments = self.comment_repository.get_all_by_article_id(article_id)
        tree = defaultdict(list)
        tree["root"] = []

        for comment in all_comments:
            if comment.comment_reply_to is None:
                key = "root"
            else:
                key = comment.comment_reply_to

            tree[key].append(comment)

        get_date = attrgetter("comment_posted_at")
        if "root" in tree:
            tree["root"].sort(key=get_date, reverse=True)

        for root in tree["root"]:
            tree[root.comment_id].sort(key=get_date)

        return dict(tree)

    def delete_comment(self, comment_id: int, user_id: int) -> bool | str:
        """
        Deletes a comment. Only an admin can delete a comment.

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

        self.comment_repository.delete(comment_id)
        return True
