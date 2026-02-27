from unittest.mock import patch

from app.models.comment_model import Comment
from tests.factories import make_account, make_article, make_comment


def test_create_comment_unauthorized(client):
    response = client.post("/comments/create/1", data={"content": "Test"}, follow_redirects=True)
    assert b"Login required." in response.data

def test_create_comment_success(client, db_session):
    user = make_account()
    db_session.add(user)
    db_session.commit()
    article = make_article(user.account_id)
    db_session.add(article)
    db_session.commit()

    with client.session_transaction() as sess:
        sess["user_id"] = user.account_id

    response = client.post(f"/comments/create/{article.article_id}", data={"content": "Mon super commentaire"}, follow_redirects=True)

    assert b"Comment added." in response.data
    comment = db_session.query(Comment).filter_by(comment_content="Mon super commentaire").first()
    assert comment is not None

def test_create_comment_on_invalid_article(client, db_session):
    user = make_account()
    db_session.add(user)
    db_session.commit()
    with client.session_transaction() as sess:
        sess["user_id"] = user.account_id

    response = client.post("/comments/create/9999", data={"content": "Error"}, follow_redirects=True)
    assert b"Error adding comment." in response.data

def test_create_reply_success(client, db_session):
    user = make_account()
    db_session.add(user)
    db_session.commit()
    article = make_article(user.account_id)
    db_session.add(article)
    db_session.commit()
    parent = make_comment(article.article_id, user.account_id, comment_content="Parent")
    db_session.add(parent)
    db_session.commit()

    with client.session_transaction() as sess:
        sess["user_id"] = user.account_id

    response = client.post(f"/comments/reply/{parent.comment_id}", data={"content": "Réponse"}, follow_redirects=True)
    assert response.status_code == 200
    reply = db_session.query(Comment).filter_by(comment_content="Réponse").first()
    assert reply is not None
    assert reply.comment_reply_to == parent.comment_id
    assert reply.comment_article_id == article.article_id

def test_create_reply_atomicity_failure(client, db_session):
    user = make_account()
    db_session.add(user)
    db_session.commit()
    article = make_article(user.account_id)
    db_session.add(article)
    db_session.commit()
    parent = make_comment(article.article_id, user.account_id, comment_content="Parent")
    db_session.add(parent)
    db_session.commit()

    with client.session_transaction() as sess:
        sess["user_id"] = user.account_id

    with patch("database.database_setup.db_session.commit") as mock_commit:
        mock_commit.side_effect = Exception("Atomic Failure")
        try:
            client.post(f"/comments/reply/{parent.comment_id}", data={"content": "My answer"})
        except Exception:
            pass

    db_session.remove()
    reply = db_session.query(Comment).filter_by(comment_content="My answer").first()
    assert reply is None

def test_delete_comment_admin_only(client, db_session):
    admin = make_account(account_username="Admin", account_role="admin")
    user = make_account(account_username="User", account_role="user")
    db_session.add_all([admin, user])
    db_session.commit()
    article = make_article(admin.account_id)
    db_session.add(article)
    db_session.commit()
    comment = make_comment(article.article_id, user.account_id)
    db_session.add(comment)
    db_session.commit()

    with client.session_transaction() as sess:
        sess["user_id"] = user.account_id
        sess["role"] = "user"
    response = client.get(f"/comments/delete/{comment.comment_id}", follow_redirects=True)
    assert b"Unauthorized" in response.data

    with client.session_transaction() as sess:
        sess["user_id"] = admin.account_id
        sess["role"] = "admin"
    response = client.get(f"/comments/delete/{comment.comment_id}", follow_redirects=True)
    assert b"Comment deleted." in response.data

def test_reply_to_non_existent_comment(client, db_session):
    user = make_account()
    db_session.add(user)
    db_session.commit()
    with client.session_transaction() as sess:
        sess["user_id"] = user.account_id

    response = client.post("/comments/reply/999", data={"content": "Hello"}, follow_redirects=True)
    assert b"Error replying" in response.data
