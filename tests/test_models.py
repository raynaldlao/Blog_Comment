from app.models import Account, Article, Feedback


def test_create_account(db_session):
    account = Account(username="pytest_user_account", email="test_account@example.com", role="user")
    db_session.add(account)
    db_session.commit()
    result = db_session.query(Account).filter_by(username="pytest_user_account").first()
    assert result is not None
    assert result.role == "user"

def test_create_article(db_session):
    author = Account(username="pytest_author_article", email="author_article@test.com", role="author")
    db_session.add(author)
    db_session.commit()
    article = Article(writer_id=author.account_id, title="Titre article", content="Contenu article")
    db_session.add(article)
    db_session.commit()
    result = db_session.query(Article).filter_by(title="Titre article").first()
    assert result is not None
    assert result.writer.username == "pytest_author_article"

def test_create_feedback(db_session):
    author = Account(username="pytest_author_feedback", email="author_feedback@test.com", role="author")
    user = Account(username="pytest_user_feedback", email="user_feedback@test.com", role="user")
    db_session.add_all([author, user])
    db_session.commit()
    article = Article(writer_id=author.account_id, title="Titre feedback", content="Contenu feedback")
    db_session.add(article)
    db_session.commit()
    feedback = Feedback(article_ref=article.article_id, commenter_id=user.account_id, message="Bravo !")
    db_session.add(feedback)
    db_session.commit()
    result = db_session.query(Feedback).filter_by(message="Bravo !").first()
    assert result is not None
    assert result.commenter.username == "pytest_user_feedback"
    assert result.article.title == "Titre feedback"
