from app.models.comment_model import Comment
from tests.factories import make_account, make_article, make_comment


def test_create_comment_with_replies(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    parent = make_comment(article.article_id, author.account_id, comment_content="Parent")
    db_session.add(parent)
    db_session.commit()
    reply = make_comment(article.article_id, author.account_id, comment_content="Child")
    reply.comment_reply_to = parent.comment_id
    db_session.add(reply)
    db_session.commit()
    db_session.refresh(parent)
    assert len(parent.comment_replies) == 1
    assert parent.comment_replies[0].comment_content == "Child"
    assert reply.reply_to_comment.comment_id == parent.comment_id


def test_cascade_delete_article_removes_comments(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    comment = make_comment(article.article_id, author.account_id)
    db_session.add(comment)
    db_session.commit()
    db_session.delete(article)
    db_session.commit()
    assert db_session.get(Comment, comment.comment_id) is None


def test_cascade_delete_parent_comment_removes_replies(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()

    parent = make_comment(article.article_id, author.account_id)
    db_session.add(parent)
    db_session.commit()

    reply = make_comment(article.article_id, author.account_id)
    reply.comment_reply_to = parent.comment_id
    db_session.add(reply)
    db_session.commit()
    db_session.delete(parent)
    db_session.commit()
    assert db_session.get(Comment, reply.comment_id) is None


def test_cascade_delete_account_removes_comments(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    comment = make_comment(article.article_id, author.account_id)
    db_session.add(comment)
    db_session.commit()
    db_session.delete(author)
    db_session.commit()
    assert db_session.get(Comment, comment.comment_id) is None
