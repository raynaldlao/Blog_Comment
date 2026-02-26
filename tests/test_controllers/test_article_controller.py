from tests.factories import make_account


def test_list_articles_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Blog" in response.data


def test_create_article_restricted(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "user"

    response = client.get("/article/new", follow_redirects=True)
    assert b"Access restricted" in response.data


def test_create_article_success(client, db_session):
    author = make_account(account_role="author")
    db_session.add(author)
    db_session.commit()

    with client.session_transaction() as sess:
        sess["user_id"] = author.account_id
        sess["role"] = "author"

    response = client.post("/article/new", data={"title": "Nouveau Titre", "content": "Contenu de l'article"}, follow_redirects=True)

    assert b"Article published!" in response.data
    from app.models.article_model import Article

    article = db_session.query(Article).filter_by(article_title="Nouveau Titre").first()
    assert article is not None
