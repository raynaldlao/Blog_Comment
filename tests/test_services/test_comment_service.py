from app.services.comment_service import CommentService
from tests.factories import make_account, make_article


def test_create_reply_logic(db_session):
    author = make_account()
    db_session.add(author)
    db_session.commit()
    article = make_article(author.account_id)
    db_session.add(article)
    db_session.commit()
    CommentService.create_comment(article.article_id, author.account_id, "Parent")
    db_session.commit()
    parent = CommentService.get_tree_by_article_id(article.article_id)[0]
    CommentService.create_reply(parent.comment_id, author.account_id, "Réponse")
    db_session.commit()
    tree = CommentService.get_tree_by_article_id(article.article_id)
    assert len(tree) == 1
    assert len(tree[0].comment_replies) == 1
    assert tree[0].comment_replies[0].comment_content == "Réponse"
