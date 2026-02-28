from typing import cast

import pytest
from sqlalchemy import exc

from app.models.article_model import Article
from tests.factories import make_account, make_article


def test_article_relationship_mapping(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article_title = "Relationship Test News"
    article = make_article(article_author_id=author.account_id, article_title=article_title)
    db_session.add(article)
    db_session.commit()
    result = db_session.get(Article, article.article_id)
    assert result.article_title == article_title
    assert result.article_author.account_id == author.account_id
    db_session.refresh(author)
    assert len(author.articles) == 1
    assert author.articles[0].article_id == article.article_id


def test_article_missing_title(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    # We intentionally pass None to test database constraints
    article = make_article(article_author_id=author.account_id, article_title=cast(str, None))
    db_session.add(article)
    with pytest.raises(exc.IntegrityError):
        db_session.commit()


def test_article_missing_content(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()

    # We intentionally pass None to test database constraints
    article = make_article(article_author_id=author.account_id, article_content=cast(str, None))
    db_session.add(article)
    with pytest.raises(exc.IntegrityError):
        db_session.commit()


def test_cascade_delete_account_removes_articles(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(article_author_id=author.account_id)
    db_session.add(article)
    db_session.commit()
    db_session.delete(author)
    db_session.commit()
    assert db_session.get(Article, article.article_id) is None
