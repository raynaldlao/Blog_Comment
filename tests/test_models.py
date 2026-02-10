import pytest
import sqlalchemy

from tests.conftest import account_model, article_model, comment_model
from tests.factories import make_account, make_article, make_comment

# --- Basic CRUD and Relationship Tests ---

def test_create_account(db_session):
    account = make_account()
    db_session.add(account)
    db_session.commit()
    Account = account_model()
    result = (
        db_session.query(Account)
        .filter_by(account_username=account.account_username)
        .first()
    )
    assert result.account_username == "Xxx__D4RK_V4D0R__xxX"
    assert result.account_password == "987654321abcdefg@"
    assert result.account_email == "C4T@exemple.com"
    assert result.account_role == "user"

def test_create_article(db_session):
    author = make_account(account_role="author")
    db_session.add(author)
    db_session.commit()
    article = make_article(article_author_id=author.account_id)
    db_session.add(article)
    db_session.commit()
    Article = article_model()
    result = (
        db_session.query(Article)
        .filter_by(article_title=article.article_title)
        .first()
    )
    expected_article_content = (
        'On the platform, Darth Vader stepped forward and spoke the truth: '
        '"Luke, I am your father." Shocked, Luke backed away, unable to accept it.'
    )
    assert result.article_author_id == 1
    assert result.article_title == "Luke, I'm your father !"
    assert result.article_content == expected_article_content
    assert result.article_author.account_role == "author"

def test_create_comment(db_session):
    author = make_account(account_role="author")
    user = make_account(
        account_username="Bob",
        account_password="2789@_124BBt",
        account_email="bob@funny.com"
    )
    db_session.add_all([author, user])
    db_session.commit()
    article = make_article(article_author_id=author.account_id)
    db_session.add(article)
    db_session.commit()
    comment = make_comment(comment_article_id=article.article_id, comment_written_account_id=user.account_id)
    db_session.add(comment)
    db_session.commit()
    Comment = comment_model()
    result = (
        db_session.query(Comment)
        .filter_by(comment_content=comment.comment_content)
        .first()
    )
    assert result.comment_article_id == 1
    assert result.comment_written_account_id == 2
    assert result.comment_author.account_username == "Bob"
    assert result.comment_author.account_password == "2789@_124BBt"
    assert result.comment_author.account_email == "bob@funny.com"
    assert result.comment_content == "Bravo !"

def test_create_comment_reply_to(db_session):
    author = make_account(account_role="author")
    user = make_account(
        account_username="Bob",
        account_password="2789@_124BBt",
        account_email="bob@funny.com"
    )
    db_session.add_all([author, user])
    db_session.commit()
    article = make_article(article_author_id=author.account_id)
    db_session.add(article)
    db_session.commit()
    parent_comment = make_comment(
        comment_article_id=article.article_id,
        comment_written_account_id=user.account_id,
        comment_content="Bravo !"
    )
    db_session.add(parent_comment)
    db_session.commit()
    reply_comment = make_comment(
        comment_article_id=article.article_id,
        comment_written_account_id=user.account_id,
        comment_content="Thank you !"
    )
    reply_comment.comment_reply_to = parent_comment.comment_id
    db_session.add(reply_comment)
    db_session.commit()
    Comment = comment_model()
    result = (
        db_session.query(Comment)
        .filter_by(comment_content=reply_comment.comment_content)
        .first()
    )
    assert result.comment_reply_to == 1
    assert result.reply_to_comment.comment_id == 1
    assert result.comment_content == "Thank you !"


# --- Business Logic Tests ---

def test_account_authenticate_success(db_session):
    account = make_account()
    db_session.add(account)
    db_session.commit()
    Account = account_model()
    result = Account.authenticate_username_password(db_session, account.account_username, account.account_password)
    assert result is not None
    assert result.account_id == account.account_id
    assert result.account_username == account.account_username
    assert result.account_password == account.account_password

def test_account_authenticate_wrong_username(db_session):
    account = make_account(account_username="GoodUser")
    db_session.add(account)
    db_session.commit()
    Account = account_model()
    result = Account.authenticate_username_password(db_session, "UnknownUser", account.account_password)
    assert result is None

def test_account_authenticate_wrong_password(db_session):
    account = make_account(account_password="GoodPassword")
    db_session.add(account)
    db_session.commit()
    Account = account_model()
    result = Account.authenticate_username_password(db_session, account.account_username, "WrongPassword")
    assert result is None

def test_account_authenticate_username_password_non_existent_user(db_session):
    Account = account_model()
    unknown_username = "ghost"
    unknown_password = "any_password"
    result = Account.authenticate_username_password(db_session, unknown_username, unknown_password)
    assert result is None


# --- Database Constraints ---

def test_account_username_unique(db_session):
    first = make_account()
    db_session.add(first)
    db_session.commit()
    second = make_account()
    db_session.add(second)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.commit()

def test_account_missing_username(db_session):
    account = make_account(account_username=None)
    db_session.add(account)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.commit()

def test_account_role_invalid(db_session):
    account = make_account(account_role="superadmin")
    db_session.add(account)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.commit()

def test_article_missing_title(db_session):
    author = make_account(account_role="author")
    db_session.add(author)
    db_session.commit()
    article = make_article(article_author_id=author.account_id, article_title=None)
    db_session.add(article)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.commit()

def test_article_missing_content(db_session):
    author = make_account(account_role="author")
    db_session.add(author)
    db_session.commit()
    article = make_article(article_author_id=author.account_id, article_content=None)
    db_session.add(article)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.commit()
