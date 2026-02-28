from app.constants import Role
from app.models.comment_model import Comment
from app.services.comment_service import CommentService
from tests.factories import make_account, make_article, make_comment


def test_create_reply_logic(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    comment_service = CommentService(db_session)
    comment_service.create_comment(article.article_id, author.account_id, "Parent")
    db_session.commit()
    parent = comment_service.get_tree_by_article_id(article.article_id)[0]
    comment_service.create_reply(parent.comment_id, author.account_id, "Reply")
    db_session.commit()
    tree = comment_service.get_tree_by_article_id(article.article_id)
    assert len(tree) == 1
    assert len(tree[0].comment_replies) == 1
    assert tree[0].comment_replies[0].comment_content == "Reply"


def test_comment_flattening_logic(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    comment_service = CommentService(db_session)
    comment_service.create_comment(article.article_id, author.account_id, "Root")
    db_session.commit()
    root = db_session.query(Comment).filter_by(comment_content="Root").first()
    comment_service.create_reply(root.comment_id, author.account_id, "Reply A")
    db_session.commit()
    reply_a = db_session.query(Comment).filter_by(comment_content="Reply A").first()
    comment_service.create_reply(reply_a.comment_id, author.account_id, "Reply B")
    db_session.commit()
    reply_b = db_session.query(Comment).filter_by(comment_content="Reply B").first()
    assert reply_b.comment_reply_to == root.comment_id
    assert len(root.comment_replies) == 2


def test_delete_comment_as_admin(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    comment = make_comment(article.article_id, author.account_id)
    db_session.add(comment)
    db_session.commit()
    comment_service = CommentService(db_session)
    result = comment_service.delete_comment(comment.comment_id, Role.ADMIN)
    db_session.commit()
    assert result == article.article_id
    assert db_session.get(Comment, comment.comment_id) is None


def test_create_comment_invalid_article(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    comment_service = CommentService(db_session)
    result = comment_service.create_comment(999, author.account_id, "Hello")
    assert result is False
