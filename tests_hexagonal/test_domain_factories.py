from datetime import datetime

from src.application.domain.account import Account, AccountRole
from src.application.domain.article import Article
from src.application.domain.comment import Comment


def create_test_account(
    account_id: int = 1,
    account_username: str = "leia",
    account_password: str = "password123",
    account_email: str = "leia@galaxy.com",
    account_role: AccountRole = AccountRole.USER,
    account_created_at: datetime | None = None,
) -> Account:
    """Factory to create a test Account entity with sensible defaults."""
    if account_created_at is None:
        account_created_at = datetime.now()

    return Account(
        account_id=account_id,
        account_username=account_username,
        account_password=account_password,
        account_email=account_email,
        account_role=account_role,
        account_created_at=account_created_at,
    )


def create_test_article(
    article_id: int = 1,
    article_author_id: int = 1,
    article_title: str = "Test Article Title",
    article_content: str = "Test article content.",
    article_published_at: datetime | None = None,
) -> Article:
    """Factory to create a test Article entity with sensible defaults."""
    if article_published_at is None:
        article_published_at = datetime.now()

    return Article(
        article_id=article_id,
        article_author_id=article_author_id,
        article_title=article_title,
        article_content=article_content,
        article_published_at=article_published_at,
    )


def create_test_comment(
    comment_id: int = 1,
    comment_article_id: int = 1,
    comment_written_account_id: int = 1,
    comment_reply_to: int | None = None,
    comment_content: str = "Test comment content.",
    comment_posted_at: datetime | None = None,
) -> Comment:
    """Factory to create a test Comment entity with sensible defaults."""
    if comment_posted_at is None:
        comment_posted_at = datetime.now()

    return Comment(
        comment_id=comment_id,
        comment_article_id=comment_article_id,
        comment_written_account_id=comment_written_account_id,
        comment_reply_to=comment_reply_to,
        comment_content=comment_content,
        comment_posted_at=comment_posted_at,
    )
