import pytest
import sqlalchemy

from app.models.account_model import Account
from app.models.article_model import Article
from app.models.comment_model import Comment
from tests.factories import make_account, make_article, make_comment

# --- Basic CRUD and Relationship Tests ---

def test_create_account(db_session):
    account = make_account(account_username="Xxx__D4RK_V4D0R__xxX")
    db_session.add(account)
    db_session.commit()

    result = db_session.query(Account).filter_by(account_username=account.account_username).first()
    assert result.account_username == "Xxx__D4RK_V4D0R__xxX"
    assert result.account_role == "user"


def test_create_article(db_session):
    author = make_account(account_role="author")
    db_session.add(author)
    db_session.commit()

    article = make_article(article_author_id=author.account_id)
    db_session.add(article)
    db_session.commit()

    result = db_session.query(Article).filter_by(article_title=article.article_title).first()
    assert result.article_author_id == author.account_id
    assert result.article_author.account_role == "author"


def test_create_comment(db_session):
    author = make_account(account_role="author")
    user = make_account(account_username="Bob")
    db_session.add_all([author, user])
    db_session.commit()

    article = make_article(article_author_id=author.account_id)
    db_session.add(article)
    db_session.commit()

    comment = make_comment(comment_article_id=article.article_id, comment_written_account_id=user.account_id)
    db_session.add(comment)
    db_session.commit()

    result = db_session.query(Comment).filter_by(comment_content="Bravo !").first()
    assert result.comment_author.account_username == "Bob"


def test_create_comment_reply_to(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()

    article = make_article(article_author_id=author.account_id)
    db_session.add(article)
    db_session.commit()

    parent = make_comment(article.article_id, author.account_id, comment_content ="Parent")
    db_session.add(parent)
    db_session.commit()

    reply = make_comment(article.article_id, author.account_id, comment_content ="Reply")
    reply.comment_reply_to = parent.comment_id
    db_session.add(reply)
    db_session.commit()

    result = db_session.query(Comment).filter_by(comment_content="Reply").first()
    assert result.comment_reply_to == parent.comment_id
    assert result.reply_to_comment.comment_content == "Parent"


# --- Database Constraints ---

def test_account_username_unique(db_session):
    first = make_account(account_username="unique")
    db_session.add(first)
    db_session.commit()

    second = make_account(account_username="unique")
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
