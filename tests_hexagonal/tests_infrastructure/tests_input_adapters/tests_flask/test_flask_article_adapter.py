from unittest.mock import Mock

from src.application.domain.account import AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.services.account_session_service import AccountSessionService
from src.application.services.article_service import ArticleService
from src.infrastructure.input_adapters.flask.flask_article_adapter import ArticleAdapter
from tests_hexagonal.test_domain_factories import create_test_account, create_test_article
from tests_hexagonal.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class ArticleAdapterTestBase(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_account_repo = Mock(spec=AccountRepository, autospec=True)
        self.mock_session_repo = Mock(spec=AccountSessionRepository, autospec=True)
        self.mock_article_repo = Mock(spec=ArticleRepository, autospec=True)
        self.mock_article_repo.count_all.return_value = 0
        self.mock_article_repo.get_paginated.return_value = []
        self.mock_session_repo.retrieve_value.return_value = None

        self.session_service = AccountSessionService(
            session_repository=self.mock_session_repo,
            account_repository=self.mock_account_repo,
        )

        self.article_service = ArticleService(
            article_repository=self.mock_article_repo,
            account_repository=self.mock_account_repo,
        )

        self.adapter = ArticleAdapter(
            article_service=self.article_service,
            session_service=self.session_service
        )

        self.article_service.get_author_name = Mock(return_value="Unknown")

        self.app.add_url_rule("/", view_func=self.adapter.list_articles, endpoint="article.list_articles")
        self.app.add_url_rule(
            "/articles/<int:article_id>",
            view_func=self.adapter.read_article,
            endpoint="article.read_article"
        )

        self.app.add_url_rule(
            "/articles/new",
            view_func=self.adapter.render_create_page,
            methods=["GET"],
            endpoint="article.render_create_page"
        )

        self.app.add_url_rule(
            "/articles/new",
            view_func=self.adapter.create_article,
            methods=["POST"],
            endpoint="article.create_article"
        )

        self.app.add_url_rule(
            "/articles/<int:article_id>/edit",
            view_func=self.adapter.render_edit_page,
            methods=["GET"],
            endpoint="article.render_edit_page"
        )

        self.app.add_url_rule(
            "/articles/<int:article_id>/edit",
            view_func=self.adapter.update_article,
            methods=["POST"],
            endpoint="article.update_article"
        )

        self.app.add_url_rule(
            "/articles/<int:article_id>/delete",
            view_func=self.adapter.delete_article,
            methods=["POST"],
            endpoint="article.delete_article"
        )

        self._register_dummy_route("/login", "auth.login", "auth")
        self._register_dummy_route("/register", "registration.register", "registration")
        self._register_dummy_route("/profile", "profile.profile", "profile")
        self._register_dummy_route("/logout", "logout.logout", "logout")

    def _login_user(self, account):
        self.mock_session_repo.retrieve_value.return_value = account.account_id
        self.mock_account_repo.get_by_id.return_value = account


class TestArticleList(ArticleAdapterTestBase):
    def test_list_articles_success(self):
        article = create_test_article(article_title="Hexagonal Architecture Rocks")
        self.mock_article_repo.get_paginated.return_value = [article]
        self.mock_article_repo.count_all.return_value = 1
        response = self.client.get("/")
        assert response.status_code == 200
        assert b"Hexagonal Architecture Rocks" in response.data

    def test_pagination_navigation_visible(self):
        self.mock_article_repo.get_paginated.return_value = [create_test_article()] * 10
        self.mock_article_repo.count_all.return_value = 15
        response = self.client.get("/")
        assert b"Next &rarr;" in response.data

    def test_article_content_truncation_on_list_view(self):
        long_content = "A" * 500
        article = create_test_article(article_content=long_content)
        self.mock_article_repo.get_paginated.return_value = [article]
        self.mock_article_repo.count_all.return_value = 1
        response = self.client.get("/")
        assert len(long_content) > 123
        assert b"AAA..." in response.data


class TestArticleDetail(ArticleAdapterTestBase):
    def test_read_article_not_found(self):
        self.mock_article_repo.get_by_id.return_value = None
        response = self.client.get("/articles/999", follow_redirects=True)
        assert b"The requested article could not be found." in response.data

    def test_ui_hides_edit_delete_buttons_for_non_owners(self):
        self.mock_article_repo.get_by_id.return_value = create_test_article(article_author_id=99)
        response = self.client.get("/articles/101")
        assert b"Edit" not in response.data
        assert b"Delete" not in response.data

    def test_xss_escaping_in_article_detail(self):
        malicious_title = "<script>alert('XSS')</script>"
        article = create_test_article(article_title=malicious_title)
        self.mock_article_repo.get_by_id.return_value = article
        response = self.client.get("/articles/1")
        assert b"<script>" not in response.data
        assert b"&lt;script&gt;" in response.data

    def test_author_username_rendered(self):
        article = create_test_article(article_title="My Awesome Article")
        self.mock_article_repo.get_by_id.return_value = article
        self.article_service.get_author_name.return_value = "KingArthur"
        response = self.client.get("/articles/1")
        assert b"KingArthur" in response.data
        assert b"99" not in response.data

    def test_seo_meta_description_rendered(self):
        content = "This is a brief summary of the article content for SEO purposes."
        article = create_test_article(article_content=content)
        self.mock_article_repo.get_by_id.return_value = article
        response = self.client.get("/articles/1")
        assert b'meta name="description"' in response.data
        assert b"This is a brief summary" in response.data



class TestArticleCreate(ArticleAdapterTestBase):
    def test_create_article_requires_login(self):
        response = self.client.post(
            "/articles/new",
            data={"title": "T", "content": "C"},
            follow_redirects=True
        )

        assert b"You must be signed in" in response.data
        self.mock_article_repo.save.assert_not_called()

    def test_create_article_validation_error(self):
        account = create_test_account(account_role=AccountRole.AUTHOR)
        self._login_user(account)

        response = self.client.post(
            "/articles/new",
            data={"title": "Hi", "content": "Valid content length."},
            follow_redirects=True
        )

        assert b"Validation Error" in response.data
        self.mock_article_repo.save.assert_not_called()

    def test_regular_user_cannot_create_article(self):
        account = create_test_account(account_role=AccountRole.USER)
        self._login_user(account)

        response = self.client.post(
            "/articles/new",
            data={"title": "Valid Title", "content": "Valid content length."},
            follow_redirects=True
        )

        assert b"Insufficient permissions" in response.data
        self.mock_article_repo.save.assert_not_called()

    def test_create_article_success(self):
        account = create_test_account(account_id=42, account_role=AccountRole.AUTHOR)
        self._login_user(account)
        self.mock_article_repo.save.return_value = None
        self.mock_article_repo.get_by_id.return_value = create_test_article(article_id=101)

        response = self.client.post(
            "/articles/new",
            data={"title": "Valid Title", "content": "Valid content length."},
            follow_redirects=True
        )
        assert b"Your article has been successfully published!" in response.data
        self.mock_article_repo.save.assert_called_once()


class TestArticleUpdate(ArticleAdapterTestBase):
    def test_update_article_unauthorized_author(self):
        account = create_test_account(account_id=42, account_role=AccountRole.AUTHOR)
        self._login_user(account)
        self.mock_article_repo.get_by_id.return_value = create_test_article(article_author_id=99)

        response = self.client.post(
            "/articles/101/edit",
            data={"title": "Hack!", "content": "Trying to edit someone else's."},
            follow_redirects=True
        )

        assert b"Unauthorized" in response.data
        self.mock_article_repo.save.assert_not_called()

    def test_update_article_success(self):
        account = create_test_account(account_id=42, account_role=AccountRole.AUTHOR)
        self._login_user(account)
        self.mock_article_repo.save.return_value = None
        self.mock_article_repo.get_by_id.return_value = create_test_article(article_author_id=42)

        response = self.client.post(
            "/articles/101/edit",
            data={"title": "Updated Title", "content": "Updated content length."},
            follow_redirects=True
        )

        assert b"Your article has been successfully updated!" in response.data
        self.mock_article_repo.save.assert_called_once()


class TestArticleDelete(ArticleAdapterTestBase):
    def test_delete_article_unauthorized_author(self):
        account = create_test_account(account_id=42, account_role=AccountRole.AUTHOR)
        self._login_user(account)
        self.mock_article_repo.get_by_id.return_value = create_test_article(article_author_id=99)
        response = self.client.post("/articles/101/delete", follow_redirects=True)
        assert b"Unauthorized" in response.data
        self.mock_article_repo.delete.assert_not_called()

    def test_admin_can_delete_any_article(self):
        account = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self._login_user(account)
        self.mock_article_repo.get_by_id.return_value = create_test_article(article_author_id=99)
        response = self.client.post("/articles/101/delete", follow_redirects=True)
        assert b"Article has been successfully deleted." in response.data
        self.mock_article_repo.delete.assert_called_once()

    def test_delete_article_success(self):
        account = create_test_account(account_id=42, account_role=AccountRole.AUTHOR)
        self._login_user(account)
        self.mock_article_repo.get_by_id.return_value = create_test_article(article_author_id=42)
        response = self.client.post("/articles/101/delete", follow_redirects=True)
        assert b"Article has been successfully deleted." in response.data
        self.mock_article_repo.delete.assert_called_once()
