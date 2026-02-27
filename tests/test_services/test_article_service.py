from app.models.article_model import Article
from app.services.article_service import ArticleService
from tests.factories import make_account, make_article


def test_create_article_service(db_session):
    author = make_account(account_role="author")
    db_session.add(author)
    db_session.commit()
    article = ArticleService.create_article("Titre", "Contenu", author.account_id)
    db_session.commit()
    assert article.article_id is not None
    assert article.article_title == "Titre"


def test_get_paginated_articles(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()

    for i in range(5):
        db_session.add(make_article(author.account_id, article_title=f"Art {i}"))

    db_session.commit()
    results = ArticleService.get_paginated_articles(page=1, per_page=3)
    assert len(results) == 3


def test_update_article_success(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id, article_title="Old Title")
    db_session.add(article)
    db_session.commit()
    result = ArticleService.update_article(article.article_id, author.account_id, "user", "New Title", "New Content")
    db_session.commit()
    assert result is not None
    assert result.article_title == "New Title"


def test_update_article_unauthorized(db_session):
    author = make_account(account_username="Author")
    wrong_user = make_account(account_username="Stranger")
    db_session.add_all([author, wrong_user])
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    result = ArticleService.update_article(article.article_id, wrong_user.account_id, "user", "Hacked", "...")
    assert result is None


def test_delete_article_by_admin(db_session):
    author = make_account()
    admin = make_account(account_username="Admin", account_role="admin")
    db_session.add_all([author, admin])
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    result = ArticleService.delete_article(article.article_id, admin.account_id, "admin")
    db_session.commit()
    assert result is True
    assert db_session.get(Article, article.article_id) is None


def test_get_total_count(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()

    for _ in range(3):
        db_session.add(make_article(author.account_id))

    db_session.commit()
    count = ArticleService.get_total_count()
    assert count == 3


def test_get_all_ordered_by_date(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    db_session.add(make_article(author.account_id, article_title="First"))
    db_session.add(make_article(author.account_id, article_title="Second"))
    db_session.commit()
    articles = ArticleService.get_all_ordered_by_date()
    assert len(articles) == 2
    assert articles[0].article_title is not None


def test_delete_article_unauthorized(db_session):
    author = make_account(account_username="Author")
    stranger = make_account(account_username="Stranger")
    db_session.add_all([author, stranger])
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    result = ArticleService.delete_article(article.article_id, stranger.account_id, "user")
    assert result is False
    assert db_session.get(Article, article.article_id) is not None
