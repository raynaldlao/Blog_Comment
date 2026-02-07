from tests.conftest import account_model, article_model, comment_model


def make_account(
    account_username="Xxx__D4RK_V4D0R__xxX",
    account_password="987654321abcdefg@",
    account_email="C4T@exemple.com",
    account_role="user",
):
    Account = account_model()
    return Account(
        account_username=account_username,
        account_password=account_password,
        account_email=account_email,
        account_role=account_role,
)

def make_article(
    article_author_id,
    article_title="Luke, I'm your father !",
    article_content=(
        'On the platform, Darth Vader stepped forward and spoke the truth: '
        '"Luke, I am your father." Shocked, Luke backed away, unable to accept it.'
    ),
):
    Article = article_model()
    return Article(
        article_author_id=article_author_id,
        article_title=article_title,
        article_content=article_content,
)

def make_comment(
    comment_article_id,
    comment_written_account_id,
    comment_content="Bravo !",
):
    Comment = comment_model()
    return Comment(
        comment_article_id=comment_article_id,
        comment_written_account_id=comment_written_account_id,
        comment_content=comment_content,
)
