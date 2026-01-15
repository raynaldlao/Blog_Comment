from app.models import Account, Article, Comment


def test_create_account(db_session):
    account = Account(account_username="pytest_user_account", account_password="123456789", account_email="test_account@example.com", account_role="user")
    db_session.add(account)
    db_session.commit()
    result = db_session.query(Account).filter_by(account_username="pytest_user_account").first()
    assert result is not None
    assert result.account_password is not None
    assert result.account_role == "user"

def test_create_article(db_session):
    author = Account(account_username="pytest_author_article", account_password="123456789", account_email="author_article@test.com", account_role="author")
    db_session.add(author)
    db_session.commit()
    article = Article(article_author_id=author.account_id, article_title="Titre article", article_content="Contenu article")
    db_session.add(article)
    db_session.commit()
    result = db_session.query(Article).filter_by(article_title="Titre article").first()
    assert result is not None
    assert result.article_author.account_username == "pytest_author_article"
    assert result.article_author.account_password is not None

def test_create_comment(db_session):
    author = Account(account_username="pytest_author_comment", account_password="123456789", account_email="author_comment@test.com", account_role="author")
    user = Account(account_username="pytest_user_comment", account_password="123456789", account_email="user_comment@test.com", account_role="user")
    db_session.add_all([author, user])
    db_session.commit()
    article = Article(article_author_id=author.account_id, article_title="Titre comment", article_content="Contenu comment")
    db_session.add(article)
    db_session.commit()
    comment = Comment(comment_article_id=article.article_id, comment_written_account_id=user.account_id, comment_content="Bravo !")
    db_session.add(comment)
    db_session.commit()
    result = db_session.query(Comment).filter_by(comment_content="Bravo !").first()
    assert result is not None
    assert result.comment_author.account_username == "pytest_user_comment"
    assert result.comment_author.account_password is not None
    assert result.comment_article.article_title == "Titre comment"
    assert result.comment_article.article_author.account_password is not None
