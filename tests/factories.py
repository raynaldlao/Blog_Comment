from app.models.account_model import Account
from app.models.article_model import Article
from app.models.comment_model import Comment


def make_account(
    account_username: str = "Xxx__D4RK_V4D0R__xxX",
    account_password: str = "password123",
    account_email: str = "vador@empire.com",
    account_role: str = "user",
) -> Account:
    """
    Factory to create an Account instance for testing.

    Args:
        account_username (str): Username.
        account_password (str): Password.
        account_email (str): Email.
        account_role (str): Role.

    Returns:
        Account: An Account instance.
    """
    return Account(
        account_username=account_username,
        account_password=account_password,
        account_email=account_email,
        account_role=account_role,
    )


def make_article(
    article_author_id: int,
    article_title: str = "Luke, I'm your father !",
    article_content: str = "On the platform, Darth Vader stepped forward...",
) -> Article:
    """
    Factory to create an Article instance for testing.

    Args:
        article_author_id (int): ID of the author account.
        article_title (str): Title.
        article_content (str): Content.

    Returns:
        Article: An Article instance.
    """
    return Article(
        article_author_id=article_author_id,
        article_title=article_title,
        article_content=article_content,
    )


def make_comment(
    comment_article_id: int,
    comment_written_account_id: int,
    comment_content: str = "Bravo !",
) -> Comment:
    """
    Factory to create a Comment instance for testing.

    Args:
        comment_article_id (int): ID of the article.
        comment_written_account_id (int): ID of the author account.
        comment_content (str): Content.

    Returns:
        Comment: A Comment instance.
    """
    return Comment(
        comment_article_id=comment_article_id,
        comment_written_account_id=comment_written_account_id,
        comment_content=comment_content,
    )
