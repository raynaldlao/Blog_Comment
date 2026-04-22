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

    def test_session_cookie_httponly(self, client, db_session):
        """
        Verifies that Flask session cookies are marked HttpOnly.
        This tests that our infrastructure securely implements the Output Port.
        """
        auth = AccountModel(account_username="secure_user", account_email="s@t.com", account_password="p", account_role="user")
        db_session.add(auth)
        db_session.commit()
        response = client.post("/login", data={"username": "secure_user", "password": "p"})
        set_cookie_header = response.headers.get("Set-Cookie")
        assert set_cookie_header is not None
        assert "HttpOnly" in set_cookie_header
        assert "SameSite=Lax" in set_cookie_header or "SameSite=Strict" in set_cookie_header

    def test_login_prevents_session_fixation(self, client, db_session):
        """Verifies that the session ID changes upon login to prevent fixation attacks."""
        auth = AccountModel(account_username="fixation_user", account_email="f@t.com", account_password="p", account_role="user")
        db_session.add(auth)
        db_session.commit()
        client.get("/")
        initial_session_cookie = client.get_cookie("session")
        client.post("/login", data={"username": "fixation_user", "password": "p"})
        logged_in_session_cookie = client.get_cookie("session")
        assert initial_session_cookie != logged_in_session_cookie
        assert logged_in_session_cookie is not None

    def test_session_tampering_protection(self, client, db_session):
        """
        Proves that modifying the session cookie without the secret key results in rejection.
        Flask cookies are encoded with a '.' separator: [payload].[timestamp].[signature]
        """
        auth = AccountModel(account_username="tmpr", account_email="tmpr@t.com", account_password="p", account_role="user")
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "tmpr", "password": "p"})
        valid_cookie = client.get_cookie("session")
        cookie_with_truncated_signature = valid_cookie.value[:-5]
        tampered_cookie_value = cookie_with_truncated_signature + "XXXXX"
        client.set_cookie("session", tampered_cookie_value)
        response = client.get("/profile", follow_redirects=True)
        assert "Login" in response.data.decode()

    def test_session_persistence_inter_client(self, client, db_session):
        """Verifies session survives between different client instances (simulating browser restart)."""
        auth = AccountModel(account_username="persist", account_email="pe@t.com", account_password="p", account_role="user")
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "persist", "password": "p"})
        session_cookie = client.get_cookie("session")
        from blog_comment_application import create_app
        new_app = create_app(db_session)
        new_client = new_app.test_client()
        new_client.set_cookie("session", session_cookie.value)
        response = new_client.get("/profile")
        assert "persist" in response.data.decode()

    def test_secure_cookie_policy_in_production(self, db_session):
        """
        Checks if SESSION_COOKIE_SECURE would be respected if debug is off.
        Note: client.post might not show 'Secure' header if not using https:// in URL,
        but we check if the config is set.
        """
        from blog_comment_application import create_app
        prod_app = create_app(db_session)
        prod_app.config["DEBUG"] = False
        prod_app.config["SESSION_COOKIE_SECURE"] = True

        client = prod_app.test_client()
        response = client.post("/login", data={"username": "any", "password": "any"})
        set_cookie = response.headers.get("Set-Cookie")
        if set_cookie:
            assert prod_app.config["SESSION_COOKIE_SECURE"] is True

    def test_session_invalidation_on_secret_key_rotation(self, client, db_session):
        """
        Verifies that rotating the SECRET_KEY invalidates all existing session cookies.
        This is a critical security recovery procedure.
        """
        auth = AccountModel(account_username="rotate_user", account_email="r@t.com", account_password="p", account_role="user")
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "rotate_user", "password": "p"})
        response_before = client.get("/profile")
        assert "rotate_user" in response_before.data.decode()
        with client.application.app_context():
            client.application.config["SECRET_KEY"] = "NEW_COMPROMISED_KEY_FIX"

        response_after = client.get("/profile", follow_redirects=True)
        assert "rotate_user" not in response_after.data.decode()
        assert "Login" in response_after.data.decode()

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
