from unittest.mock import patch

from app.constants import Role, SessionKey
from app.models.article_model import Article
from tests.factories import make_account, make_article


def test_list_articles_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Blog" in response.data


def test_view_article_success(client, db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id, article_title="Titre de Test")
    db_session.add(article)
    db_session.commit()

    response = client.get(f"/article/{article.article_id}")
    assert response.status_code == 200
    assert b"Titre de Test" in response.data


def test_view_article_not_found(client):
    response = client.get("/article/999", follow_redirects=True)
    assert b"Article not found." in response.data


def test_create_article_restricted(client):
    with client.session_transaction() as sess:
        sess[SessionKey.USER_ID] = 1
        sess[SessionKey.ROLE] = Role.USER

    response = client.get("/article/new", follow_redirects=True)
    assert b"Access restricted" in response.data


def test_create_article_success(client, db_session):
    author = make_account(account_role=Role.AUTHOR)
    db_session.add(author)
    db_session.commit()

    with client.session_transaction() as sess:
        sess[SessionKey.USER_ID] = author.account_id
        sess[SessionKey.ROLE] = Role.AUTHOR

    response = client.post("/article/new", data={"title": "Nouveau Titre", "content": "Contenu"}, follow_redirects=True)
    assert b"Article published!" in response.data
    article = db_session.query(Article).filter_by(article_title="Nouveau Titre").first()
    assert article is not None


def test_create_article_atomicity_failure(client, db_session):
    author = make_account(account_role=Role.AUTHOR)
    db_session.add(author)
    db_session.commit()

    with client.session_transaction() as sess:
        sess[SessionKey.USER_ID] = author.account_id
        sess[SessionKey.ROLE] = Role.AUTHOR

    with patch("database.database_setup.db_session.commit") as mock_commit:
        mock_commit.side_effect = Exception("Database Failure")
        try:
            client.post("/article/new", data={"title": "Ghost Article", "content": "Text"})
        except Exception:
            pass

    db_session.remove()
    article = db_session.query(Article).filter_by(article_title="Ghost Article").first()
    assert article is None


def test_edit_article_unauthorized(client, db_session):
    author1 = make_account(account_username="Author1", account_role=Role.AUTHOR)
    author2 = make_account(account_username="Author2", account_role=Role.AUTHOR)
    db_session.add_all([author1, author2])
    db_session.commit()

    article = make_article(author1.account_id, article_title="Original")
    db_session.add(article)
    db_session.commit()

    with client.session_transaction() as sess:
        sess[SessionKey.USER_ID] = author2.account_id
        sess[SessionKey.ROLE] = Role.AUTHOR

    response = client.post(f"/article/{article.article_id}/edit", data={"title": "Hack", "content": "Hack"}, follow_redirects=True)
    assert b"Update failed" in response.data
    db_session.remove()
    assert db_session.get(Article, article.article_id).article_title == "Original"


def test_delete_article_success(client, db_session):
    author = make_account(account_role=Role.ADMIN)
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()

    with client.session_transaction() as sess:
        sess[SessionKey.USER_ID] = author.account_id
        sess[SessionKey.ROLE] = Role.ADMIN

    response = client.get(f"/article/{article.article_id}/delete", follow_redirects=True)
    assert b"Article deleted" in response.data
    db_session.remove()
    assert db_session.get(Article, article.article_id) is None


def test_list_articles_pagination(client, db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()

    for i in range(12):
        db_session.add(make_article(article_author_id=author.account_id, article_title=f"Article_{i:02d}"))

    db_session.commit()
    response = client.get("/?page=2")
    assert response.status_code == 200
    assert b"Article_00" in response.data
    assert b"Article_01" in response.data
    assert b"Article_11" not in response.data


def test_edit_article_not_found(client):
    with client.session_transaction() as sess:
        sess[SessionKey.USER_ID] = 1
        sess[SessionKey.ROLE] = Role.ADMIN

    response = client.get("/article/999/edit", follow_redirects=True)
    assert response.status_code == 200
    assert b"Article not found" in response.data


def test_edit_article_success_by_author(client, db_session):
    author = make_account(account_role=Role.AUTHOR)
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id, article_title="Ancien Titre")
    db_session.add(article)
    db_session.commit()

    with client.session_transaction() as sess:
        sess[SessionKey.USER_ID] = author.account_id
        sess[SessionKey.ROLE] = Role.AUTHOR

    response = client.post(f"/article/{article.article_id}/edit", data={"title": "Titre Modifié", "content": "Nouveau contenu"}, follow_redirects=True)

    assert b"Article updated!" in response.data
    db_session.refresh(article)
    assert article.article_title == "Titre Modifié"


def test_admin_cannot_edit_others_article(client, db_session):
    author = make_account(account_username="Auteur")
    admin = make_account(account_username="Admin", account_role=Role.ADMIN)
    db_session.add_all([author, admin])
    db_session.commit()
    article = make_article(author.account_id, article_title="Titre Intouchable")
    db_session.add(article)
    db_session.commit()

    with client.session_transaction() as sess:
        sess[SessionKey.USER_ID] = admin.account_id
        sess[SessionKey.ROLE] = Role.ADMIN

    response = client.post(f"/article/{article.article_id}/edit", data={"title": "Hack par Admin", "content": "..."}, follow_redirects=True)

    assert b"Update failed" in response.data
    db_session.refresh(article)
    assert article.article_title == "Titre Intouchable"


def test_delete_article_success_by_author(client, db_session):
    author = make_account(account_role=Role.AUTHOR)
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()

    with client.session_transaction() as sess:
        sess[SessionKey.USER_ID] = author.account_id
        sess[SessionKey.ROLE] = Role.AUTHOR

    response = client.get(f"/article/{article.article_id}/delete", follow_redirects=True)
    assert b"Article deleted" in response.data
    db_session.remove()
    assert db_session.get(Article, article.article_id) is None
