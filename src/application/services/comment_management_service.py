from datetime import datetime

from src.application.domain.account import Account
from src.application.domain.comment import Comment
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.output_ports.comment_repository import CommentRepository


class CommentManagementService:
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
        """
        self.comment_repository = comment_repository
        self.article_repository = article_repository
        self.account_repository = account_repository

    def _get_authorized_account(self, user_id: int) -> Account | str:
        """
        Helper method to retrieve and validate an account.
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
        account_or_error = self._get_authorized_account(user_id)
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
