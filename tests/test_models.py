import pytest
from app.models import Account, Article, Comment


@pytest.fixture
def account_data():
    return {
        "account_username": "pytest_user_account",
        "account_password": "123456789",
        "account_email": "test_account@example.com",
        "account_role": "user"
    }

@pytest.fixture
def article_data():
    return {
        "article_title": "Test Article",
        "article_content": "This is a test article."
    }


def test_create_account(db_session, account_data):
    account = Account(
        account_username=account_data["account_username"],
        account_password=account_data["account_password"],
        account_email=account_data["account_email"],
        account_role=account_data["account_role"]
    )

    db_session.add(account)
    db_session.commit()

    result = (
        db_session.query(Account)
        .filter_by(account_username=account_data["account_username"])
        .first()
    )

    assert result is not None
    assert result.account_username is not None
    assert result.account_password is not None
    assert result.account_role is not None
    assert result.account_username == "pytest_user_account"
    assert result.account_password == "123456789"
    assert result.account_role == "user"

def test_create_article(db_session, account_data, article_data):
    author = Account(
        account_username=account_data["account_username"],
        account_password=account_data["account_password"],
        account_email=account_data["account_email"],
        account_role="author"
    )

    db_session.add(author)
    db_session.commit()

    article = Article(
        article_author_id=author.account_id,
        article_title=article_data["article_title"],
        article_content=article_data["article_content"]
    )

    db_session.add(article)
    db_session.commit()

    result = (
        db_session.query(Article)
        .filter_by(article_title=article_data["article_title"])
        .first()
    )

    assert result is not None
    assert result.article_author_id is not None
    assert result.article_title is not None
    assert result.article_content is not None
    assert result.article_author.account_username == "pytest_user_account"
    assert result.article_author.account_password == "123456789"
    assert result.article_author.account_role == "author"

def test_create_comment(db_session, account_data, article_data):
    author = Account(
        account_username=account_data["account_username"],
        account_password=account_data["account_password"],
        account_email= account_data["account_email"],
        account_role="author" 
    )

    user = Account(
        account_username="Bob",
        account_password="2789@_124BBt",
        account_email= "bob@humour.fr",
        account_role=account_data["account_role"]
    )

    db_session.add_all([author, user])
    db_session.commit()

    article = Article(
        article_author_id = author.account_id,
        article_title= article_data["article_title"],
        article_content=article_data["article_content"]
    )

    db_session.add(article)
    db_session.commit()

    comment = Comment(
        comment_article_id=article.article_id,
        comment_written_account_id=user.account_id,
        comment_content="Bravo !"
    )

    db_session.add(comment)
    db_session.commit()

    result = db_session.query(Comment).filter_by(comment_content="Bravo !").first()

    assert result is not None
    assert result.comment_article_id is not None
    assert result.comment_content is not None
    assert result.comment_author.account_username == "Bob"
    assert result.comment_article.article_title == "Test Article"
    assert result.comment_article.article_author.account_password is not None
