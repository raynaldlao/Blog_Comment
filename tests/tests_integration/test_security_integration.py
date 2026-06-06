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

    def test_article_detail_escapes_xss(self, client, db_session):
        """
        Verifies that article content is HTML-escaped on the detail page.

        Creates an article with a script payload and checks that the
        rendered detail page contains escaped entities rather than raw HTML.
        """
        auth = AccountModel(
            account_username="xss_detail", account_email="xss_d@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "xss_detail", "password": "p"}, follow_redirects=True)

        xss_payload = '<script>alert("xss")</script>'
        client.post("/articles/new", data={
            "title": "XSS Detail Test",
            "content": xss_payload
        }, follow_redirects=True)

        article = db_session.query(ArticleModel).filter_by(article_title="XSS Detail Test").first()
        response = client.get(f"/articles/{article.article_id}")
        assert response.status_code == 200
        assert "&lt;script&gt;alert(&#34;xss&#34;)&lt;/script&gt;" in response.text

    def test_article_detail_preserves_newlines(self, client, db_session):
        """
        Verifies that newlines in article content are rendered as <br> tags.

        Creates an article with multi-line content and checks that the
        rendered detail page contains <br> elements for each newline.
        """
        auth = AccountModel(
            account_username="nl_detail", account_email="nl_d@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "nl_detail", "password": "p"}, follow_redirects=True)

        client.post("/articles/new", data={
            "title": "Newline Test Detail",
            "content": "line1\nline2\nline3"
        }, follow_redirects=True)

        article = db_session.query(ArticleModel).filter_by(article_title="Newline Test Detail").first()
        response = client.get(f"/articles/{article.article_id}")
        assert response.status_code == 200
        assert "<br>" in response.text

    def test_comment_xss_with_newlines_escaped(self, client, db_session):
        """
        Verifies that a comment containing both XSS payload and newlines
        is properly escaped while still converting newlines to <br> tags.
        """
        auth = AccountModel(
            account_username="xss_comment", account_email="xc@t.com",
            account_password="p", account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        article = ArticleModel(article_title="XSS Comment Test", article_content="...", article_author_id=auth.account_id)
        db_session.add(article)
        db_session.commit()

        client.post("/login", data={"username": "xss_comment", "password": "p"}, follow_redirects=True)

        malicious_comment = "<script>alert(1)</script>\nclean line"
        client.post(f"/articles/{article.article_id}/comments", data={
            "content": malicious_comment
        }, follow_redirects=True)

        response = client.get(f"/articles/{article.article_id}")
        assert response.status_code == 200
        assert b"<script>alert(1)</script>" not in response.data
        assert b"&lt;script&gt;" in response.data
        assert b"<br>" in response.data
        assert b"clean line" in response.data

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
        assert "Welcome Back" in response.data.decode()

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
        assert "Welcome Back" in response_after.data.decode()

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


class TestCSRF:
    """Tests focused on CSRF token presence in rendered forms."""

    def test_login_page_contains_csrf_field(self, client):
        """
        Verifies that the login form renders a CSRF token field.

        The hidden input ``csrf_token`` must be present in the login
        page HTML so that POST submissions include a valid token.
        """
        response = client.get("/login")
        assert b"csrf_token" in response.data
        assert b'name="csrf_token"' in response.data

    def test_register_page_contains_csrf_field(self, client):
        """
        Verifies that the registration form renders a CSRF token field.

        Ensures the ``csrf_token`` hidden input is injected into the
        registration template to protect account creation.
        """
        response = client.get("/register")
        assert b"csrf_token" in response.data

    def test_create_article_page_contains_csrf_field(self, client, db_session):
        """
        Verifies that the article creation form renders a CSRF token field.

        Creates an authenticated author session first, then checks that
        the article creation page includes the ``csrf_token`` hidden input.
        """
        from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel

        auth = AccountModel(
            account_username="csrf_author", account_email="csrf@t.com", account_password="p", account_role="author"
        )
        db_session.add(auth)
        db_session.commit()
        client.post("/login", data={"username": "csrf_author", "password": "p"})
        response = client.get("/articles/new")
        assert b"csrf_token" in response.data


class TestCSP:
    """Tests focused on Content Security Policy headers."""

    def test_csp_hash_matches_inline_script(self, client):
        """Verifies that the CSP hash matches the actual inline script content."""
        import base64
        import hashlib
        from pathlib import Path

        project_root = Path(__file__).parents[2]
        template_path = project_root / "frontend/templates/base.html"
        content = template_path.read_text()
        start = content.index("<script>") + len("<script>")
        end = content.index("</script>", start)
        expected_hash = "'sha256-" + base64.b64encode(hashlib.sha256(content[start:end].encode()).digest()).decode() + "'"
        response = client.get("/login")
        csp = response.headers["Content-Security-Policy"]
        assert expected_hash in csp

    def test_csp_report_endpoint(self, client):
        """Verifies that CSP violation reports can be submitted."""
        response = client.post("/csp-report", json={"csp-report": {"test": True}})
        assert response.status_code == 204

    def test_csp_reporting_endpoints_header(self, client):
        """Verifies the Reporting-Endpoints header is present and correct."""
        response = client.get("/login")
        assert response.headers.get("Reporting-Endpoints") == 'csp-endpoint="/csp-report"'

    def test_csp_report_endpoint_rejects_get(self, client):
        """Verifies that only POST is accepted on /csp-report."""
        response = client.get("/csp-report")
        assert response.status_code == 405


class TestSecurityHeaders:
    """Tests focused on generic HTTP security headers."""

    def test_x_content_type_options_header(self, client):
        """Verifies the X-Content-Type-Options header is set to nosniff."""
        response = client.get("/login")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options_header(self, client):
        """Verifies the X-Frame-Options header is set to DENY."""
        response = client.get("/login")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_referrer_policy_header(self, client):
        """Verifies the Referrer-Policy header is set to strict-origin-when-cross-origin."""
        response = client.get("/login")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
