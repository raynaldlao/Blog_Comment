from app.models.account_model import Account
from app.models.article_model import Article
from app.models.comment_model import Comment


def make_account(
    account_username="Xxx__D4RK_V4D0R__xxX",
    account_password="password123",
    account_email="vador@empire.com",
    account_role="user",
):
    return Account(
        account_username=account_username,
        account_password=account_password,
        account_email=account_email,
        account_role=account_role,
    )

def make_article(article_author_id, article_title="Luke, I'm your father !", article_content="On the platform, Darth Vader stepped forward..."):
    return Article(
        article_author_id=article_author_id,
        article_title=article_title,
        article_content=article_content,
    )

def make_comment(comment_article_id, comment_written_account_id, comment_content="Bravo !"):
    return Comment(
        comment_article_id=comment_article_id,
        comment_written_account_id=comment_written_account_id,
        comment_content=comment_content,
    )
