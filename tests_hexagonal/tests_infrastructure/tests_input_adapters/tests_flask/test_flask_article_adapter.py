from unittest.mock import Mock

from src.application.domain.account import AccountRole
from src.application.output_ports.article_repository import ArticleRepository
from src.application.services.article_service import ArticleService
from src.infrastructure.input_adapters.flask.flask_article_adapter import ArticleAdapter
from tests_hexagonal.test_domain_factories import create_test_account, create_test_article
from tests_hexagonal.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class ArticleAdapterTestBase(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_article_repo = Mock(spec=ArticleRepository, autospec=True)
        self.mock_article_repo.count_all.return_value = 0
        self.mock_article_repo.get_paginated.return_value = []
        self.mock_account_repo = Mock()

        self.article_service = ArticleService(
            article_repository=self.mock_article_repo,
            account_repository=self.mock_account_repo,
        )

        self.adapter = ArticleAdapter(article_service=self.article_service)
        self.mock_account_repo.get_by_id.return_value = None
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
        self._register_dummy_route("/logout", "logout.logout", "logout")
        self._register_dummy_route("/profile", "profile.profile", "profile")

    def _prepare_user_context(self, account):
        """Helper to set current user in g AND make account repo return it."""
        self.set_current_user(account)
        self.mock_account_repo.get_by_id.return_value = account

class TestArticleAnonymousAccess(ArticleAdapterTestBase):
    def test_list_articles_as_anonymous(self):
        article = create_test_article(article_title="Hexagonal Secrets")
        self.mock_article_repo.get_paginated.return_value = [article]
        self.mock_article_repo.count_all.return_value = 1

        response = self.client.get("/")
        assert response.status_code == 200
        assert b"Hexagonal Secrets" in response.data
        assert b"Write Article" not in response.data

    def test_read_article_as_anonymous(self):
        article = create_test_article(article_title="Public View")
        self.mock_article_repo.get_by_id.return_value = article

        response = self.client.get("/articles/1")
        assert response.status_code == 200
        assert b"Public View" in response.data
        assert b"Edit" not in response.data
        assert b"Delete" not in response.data

    def test_create_article_redirects_anonymous_to_login(self):
        response = self.client.post("/articles/new", data={"title": "T", "content": "C"}, follow_redirects=True)
        assert b"You must be signed in" in response.data
        assert b"auth" in response.data

class TestArticleAuthorAccess(ArticleAdapterTestBase):
    def test_author_can_create_article(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        created_article = create_test_article(article_id=0, article_author_id=10, article_title="My First Post")
        self.mock_article_repo.get_by_id.return_value = created_article

        response = self.client.post(
            "/articles/new",
            data={"title": "My First Post", "content": "Content is long enough now for validation."},
            follow_redirects=True
        )

        assert b"Your article has been successfully published!" in response.data
        assert b"My First Post" in response.data
        self.mock_article_repo.save.assert_called_once()

    def test_author_can_edit_own_article(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        article = create_test_article(article_id=1, article_author_id=10)
        self.mock_article_repo.get_by_id.return_value = article

        response = self.client.post(
            "/articles/1/edit",
            data={"title": "Updated Title", "content": "New content is long enough for validation."},
            follow_redirects=True
        )

        assert b"Your article has been successfully updated!" in response.data
        self.mock_article_repo.save.assert_called_once()

    def test_author_cannot_edit_others_article(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        other_article = create_test_article(article_id=1, article_author_id=99)
        self.mock_article_repo.get_by_id.return_value = other_article

        response = self.client.post(
            "/articles/1/edit",
            data={"title": "Hack Attack", "content": "Trying to edit other's content."},
            follow_redirects=True
        )

        assert b"Unauthorized" in response.data
        self.mock_article_repo.save.assert_not_called()

class TestArticleAdminAccess(ArticleAdapterTestBase):
    def test_admin_can_delete_any_article(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self._prepare_user_context(admin)
        article = create_test_article(article_id=1, article_author_id=99)
        self.mock_article_repo.get_by_id.return_value = article
        response = self.client.post("/articles/1/delete", follow_redirects=True)
        assert b"Article has been successfully deleted." in response.data
        self.mock_article_repo.delete.assert_called_once()

class TestArticleValidation(ArticleAdapterTestBase):
    def test_create_article_validation_fail(self):
        author = create_test_account(account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)

        response = self.client.post(
            "/articles/new",
            data={"title": "To Short", "content": "Short"},
            follow_redirects=True
        )

        assert b"Validation Error" in response.data
        self.mock_article_repo.save.assert_not_called()
