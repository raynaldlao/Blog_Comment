from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel


class TestXSS:
    """Tests focused on preventing Cross-Site Scripting vulnerabilities."""

    def test_xss_protection_integ(self, client, db_session):
        """
        Verifies that the app escapes HTML/Script tags to prevent XSS.
        """
        auth = AccountModel(account_username="xss_author", account_email="xss@t.com", account_password="p", account_role="author")
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "xss_author", "password": "p"}, follow_redirects=True)
        xss_payload = "<script>alert('XSS')</script>"

        client.post("/articles/new", data={
            "title": "Malicious Article",
            "content": xss_payload
        }, follow_redirects=True)

        response = client.get("/")
        assert xss_payload.encode() not in response.data
        assert b"&lt;script&gt;" in response.data or b"alert('XSS')" in response.data

class TestSQLi:
    """Tests focused on preventing SQL Injection vulnerabilities."""

    def test_sql_injection_resilience_integ(self, client, db_session):
        """
        Verifies that malicious SQL input is correctly escaped by SQLAlchemy/Postgres.
        """
        auth = AccountModel(account_username="db_admin", account_email="db@t.com", account_password="p", account_role="author")
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "db_admin", "password": "p"}, follow_redirects=True)
        malicious_title = "Safe Title'); DROP TABLE accounts; --"

        client.post("/articles/new", data={
            "title": malicious_title,
            "content": "Checking resilience..."
        }, follow_redirects=True)

        assert db_session.query(AccountModel).count() >= 1
        saved_article = db_session.query(ArticleModel).filter_by(article_title=malicious_title).first()
        assert saved_article is not None
        assert saved_article.article_title == malicious_title

    def test_sql_injection_in_login_integ(self, client, db_session):
        """
        Verifies that 'always true' SQL injections in login don't work.
        """
        response = client.post("/login", data={
            "username": "' OR '1'='1",
            "password": "any"
        }, follow_redirects=True)
        assert b"Invalid username or password" in response.data

class TestAccessControl:
    """Tests focused on enforcing authorization and permission boundaries."""

    def test_unauthorized_article_deletion(self, client, db_session):
        """
        Ensures that a user cannot delete another author's article.
        """
        author = AccountModel(account_username="author1", account_email="a1@t.com", account_password="p", account_role="author")
        malicious = AccountModel(account_username="hacker", account_email="h@t.com", account_password="p", account_role="user")
        db_session.add(author)
        db_session.add(malicious)
        db_session.commit()
        article = ArticleModel(article_title="Secret", article_content="...", article_author_id=author.account_id)
        db_session.add(article)
        db_session.commit()
        client.post("/login", data={"username": "hacker", "password": "p"}, follow_redirects=True)
        response = client.post(f"/articles/{article.article_id}/delete", follow_redirects=True)
        assert b"Insufficient permissions" in response.data or b"Unauthorized" in response.data
        assert db_session.query(ArticleModel).filter_by(article_id=article.article_id).count() == 1

    def test_read_non_existent_article(self, client, db_session):
        """
        Verifies error handling for non-existent IDs.
        """
        response = client.get("/articles/99999", follow_redirects=True)
        assert b"Article not found" in response.data
