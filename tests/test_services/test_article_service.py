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
