from tests.factories import make_account, make_article


def test_create_comment_flow(client, db_session):
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
    from app.models.comment_model import Comment

    comment = db_session.query(Comment).filter_by(comment_content="Mon super commentaire").first()
    assert comment is not None
