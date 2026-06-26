import json
from unittest.mock import Mock

from src.application.domain.account import AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.output_ports.comment_repository import CommentRepository
from src.application.services.article_service import ArticleService
from src.infrastructure.input_adapters.flask.flask_article_adapter import ArticleAdapter
from tests.test_domain_factories import create_test_account, create_test_article
from tests.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class ArticleAdapterTestBase(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_article_repo = Mock(spec=ArticleRepository, autospec=True)
        self.mock_article_repo.count_all.return_value = 0
        self.mock_article_repo.get_paginated.return_value = []
        self.mock_account_repo = Mock(spec=AccountRepository, autospec=True)
        self.mock_account_repo.get_by_ids.return_value = []
        self.mock_comment_repo = Mock(spec=CommentRepository, autospec=True)
        self.mock_comment_repo.get_all_by_article_id.return_value = []

        self.article_service = ArticleService(
            article_repository=self.mock_article_repo,
            account_repository=self.mock_account_repo,
            comment_repository=self.mock_comment_repo
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
            "/articles/<int:article_id>/edit",
            view_func=self.adapter.render_edit_page,
            methods=["GET"],
            endpoint="article.render_edit_page"
        )

        self.app.add_url_rule(
            "/api/articles",
            view_func=self.adapter.api_create_article,
            methods=["POST"],
            endpoint="article.api_create",
        )
        self.app.add_url_rule(
            "/api/articles/<int:article_id>",
            view_func=self.adapter.api_get_article,
            methods=["GET"],
            endpoint="article.api_get",
        )
        self.app.add_url_rule(
            "/api/articles/<int:article_id>",
            view_func=self.adapter.api_update_article,
            methods=["PUT"],
            endpoint="article.api_update",
        )
        self.app.add_url_rule(
            "/api/articles/<int:article_id>",
            view_func=self.adapter.api_delete_article,
            methods=["DELETE"],
            endpoint="article.api_delete",
        )

        self._register_dummy_route("/login", "auth.login", "auth")
        self._register_dummy_route("/register", "registration.register", "registration")
        self._register_dummy_route("/logout", "auth.logout", "logout")
        self._register_dummy_route("/profile", "auth.profile", "profile")
        self._register_dummy_route("/articles/<int:article_id>/comments", "comment.create_comment", "comment")
        self._register_dummy_route(
            "/articles/<int:article_id>/comments/<int:parent_comment_id>/reply",
            "comment.reply_to_comment",
            "comment"
        )
        self._register_dummy_route(
            "/articles/<int:article_id>/comments/<int:comment_id>/delete",
            "comment.delete_comment",
            "comment"
        )

    def _prepare_user_context(self, account):
        self.set_current_user(account)
        self.mock_account_repo.get_by_id.return_value = account


class TestArticleAnonymousAccess(ArticleAdapterTestBase):
    def test_list_articles_as_anonymous(self):
        article = create_test_article(article_title="Hexagonal Secrets", article_author_id=1)
        self.mock_article_repo.get_paginated.return_value = [article]
        self.mock_article_repo.count_all.return_value = 1
        self.mock_account_repo.get_by_ids.return_value = [create_test_account(account_id=1, account_username="Author")]
        response = self.client.get("/")
        assert response.status_code == 200
        assert b"Hexagonal Secrets" in response.data

    def test_read_article_as_anonymous(self):
        article = create_test_article(article_title="Public View", article_author_id=1)
        self.mock_article_repo.get_by_id.return_value = article
        self.mock_comment_repo.get_all_by_article_id.return_value = []
        self.mock_account_repo.get_by_id.return_value = create_test_account(account_id=1, account_username="Author")
        response = self.client.get("/articles/1")
        assert response.status_code == 200
        assert b"Public View" in response.data

    def test_list_articles_date_rendering(self):
        from datetime import datetime
        publication_date = datetime(2026, 4, 29)

        article = create_test_article(
            article_id=1,
            article_author_id=1,
            article_title="Date Test",
            article_published_at=publication_date
        )

        self.mock_article_repo.get_paginated.return_value = [article]
        self.mock_article_repo.count_all.return_value = 1
        self.mock_account_repo.get_by_ids.return_value = [create_test_account(account_id=1, account_username="Author")]
        response = self.client.get("/")
        assert response.status_code == 200
        assert b"Apr 29, 2026" in response.data
        assert b'datetime="2026-04-29"' in response.data

    def test_list_articles_no_date_hides_meta(self):
        article = create_test_article(
            article_id=1,
            article_author_id=1,
            article_title="No Date Article",
        )

        article.article_published_at = None
        self.mock_article_repo.get_paginated.return_value = [article]
        self.mock_article_repo.count_all.return_value = 1
        self.mock_account_repo.get_by_ids.return_value = [create_test_account(account_id=1, account_username="Author")]
        response = self.client.get("/")
        assert response.status_code == 200
        assert b"meta-date" not in response.data

    def test_list_articles_contains_jump_modal(self):
        self.mock_article_repo.get_paginated.return_value = []
        self.mock_article_repo.count_all.return_value = 0
        response = self.client.get("/")
        assert response.status_code == 200
        assert b'<dialog id="jump-modal"' in response.data
        assert b"pagination.js" in response.data
        assert b"data-total-pages" in response.data
        assert b"data-url" in response.data

    def test_create_article_redirects_anonymous_to_login(self):
        response = self.client.post("/api/articles", json={"title": "T", "content": "C"})
        assert response.status_code == 401
        assert response.get_json() == {"error": "Unauthorized."}

    def test_render_create_page_redirects_anonymous_to_login(self):
        response = self.client.get("/articles/new", follow_redirects=True)
        assert b"You must be signed in" in response.data
        assert b"alert-error" in response.data

    def test_delete_article_redirects_anonymous_to_login(self):
        response = self.client.delete("/api/articles/1")
        assert response.status_code == 401
        assert response.get_json() == {"error": "Unauthorized."}

    def test_render_edit_page_redirects_anonymous_to_login(self):
        response = self.client.get("/articles/1/edit", follow_redirects=True)
        assert b"You must be signed in" in response.data
        assert b"alert-error" in response.data

    def test_update_article_redirects_anonymous_to_login(self):
        response = self.client.put("/api/articles/1", json={"title": "T", "content": "C"})
        assert response.status_code == 401
        assert response.get_json() == {"error": "Unauthorized."}


class TestArticleUserAccess(ArticleAdapterTestBase):
    def test_user_cannot_access_create_page(self):
        user = create_test_account(account_id=10, account_role=AccountRole.USER)
        self._prepare_user_context(user)
        response = self.client.get("/articles/new", follow_redirects=True)
        assert b"Insufficient permissions" in response.data
        assert b"alert-error" in response.data

    def test_user_cannot_access_edit_page(self):
        user = create_test_account(account_id=10, account_role=AccountRole.USER)
        self._prepare_user_context(user)
        response = self.client.get("/articles/1/edit", follow_redirects=True)
        assert b"Insufficient permissions" in response.data
        assert b"alert-error" in response.data

    def test_user_cannot_update_article(self):
        user = create_test_account(account_id=10, account_role=AccountRole.USER)
        self._prepare_user_context(user)
        response = self.client.put("/api/articles/1", json={"title": "T", "content": "C"})
        assert response.status_code == 403
        assert response.get_json() == {"error": "Insufficient permissions."}

    def test_user_cannot_delete_article(self):
        user = create_test_account(account_id=10, account_role=AccountRole.USER)
        self._prepare_user_context(user)
        response = self.client.delete("/api/articles/1")
        assert response.status_code == 403
        assert response.get_json() == {"error": "Insufficient permissions."}

    def test_user_cannot_create_article(self):
        user = create_test_account(account_id=10, account_role=AccountRole.USER)
        self._prepare_user_context(user)
        response = self.client.post("/api/articles", json={"title": "T", "content": "C"})
        assert response.status_code == 403
        assert response.get_json() == {"error": "Insufficient permissions."}
        self.mock_article_repo.save.assert_not_called()


class TestArticleAuthorAccess(ArticleAdapterTestBase):
    def test_author_can_create_article_with_short_title(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)

        def _save_side_effect(article):
            article.article_id = 1

        self.mock_article_repo.save.side_effect = _save_side_effect

        response = self.client.post(
            "/api/articles",
            json={"title": "A", "content": "Contenu suffisant."},
        )

        assert response.status_code == 201
        assert response.get_json() == {"id": 1}
        self.mock_article_repo.save.assert_called_once()

    def test_author_create_article_service_error(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        mock_service = Mock(spec=ArticleService)
        self.adapter.article_service = mock_service
        mock_service.create_article.return_value = "Service Error Message"

        response = self.client.post(
            "/api/articles",
            json={"title": "A", "content": "Long enough content."},
        )
        assert response.status_code == 403
        assert response.get_json() == {"error": "Service Error Message"}

    def test_author_can_edit_own_article(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        article = create_test_article(article_id=1, article_author_id=10)
        self.mock_article_repo.get_by_id.return_value = article

        response = self.client.put(
            "/api/articles/1",
            json={"title": "Updated Title", "content": "New content is long enough."},
        )

        assert response.status_code == 200
        assert response.get_json() == {"ok": True}
        self.mock_article_repo.save.assert_called_once()

    def test_author_cannot_edit_others_article(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        other_article = create_test_article(article_id=1, article_author_id=99)
        self.mock_article_repo.get_by_id.return_value = other_article

        response = self.client.put(
            "/api/articles/1",
            json={"title": "Hack Attempt", "content": "I am not the author."},
        )

        assert response.status_code == 403
        assert "Unauthorized" in response.get_json()["error"]
        self.mock_article_repo.save.assert_not_called()

    def test_read_article_not_found(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        self.mock_article_repo.get_by_id.return_value = None
        response = self.client.get("/articles/999", follow_redirects=True)
        assert b"Error: Article not found." in response.data
        assert b"alert-error" in response.data

    def test_render_edit_page_not_found(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        self.mock_article_repo.get_by_id.return_value = None

        response = self.client.get("/articles/999/edit", follow_redirects=True)
        assert b"Error: The requested article could not be found." in response.data
        assert b"alert-error" in response.data


class TestArticleAdminAccess(ArticleAdapterTestBase):
    def test_admin_can_delete_any_article(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self._prepare_user_context(admin)
        article = create_test_article(article_id=1, article_author_id=99)
        self.mock_article_repo.get_by_id.return_value = article
        response = self.client.delete("/api/articles/1")
        assert response.status_code == 200
        assert response.get_json() == {"ok": True}
        self.mock_article_repo.delete.assert_called_once()


class TestArticleValidation(ArticleAdapterTestBase):
    def test_create_article_fails_if_field_missing(self):
        author = create_test_account(account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)

        response = self.client.post(
            "/api/articles",
            json={"title": "Title Only"},
        )

        assert response.status_code == 400
        assert "1 character" in response.get_json()["error"]
        self.mock_article_repo.save.assert_not_called()

    def test_update_article_validation_error(self):
        author = create_test_account(account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        article = create_test_article(article_id=1, article_author_id=author.account_id)
        self.mock_article_repo.get_by_id.return_value = article

        response = self.client.put(
            "/api/articles/1",
            json={"title": "", "content": ""},
        )

        assert response.status_code == 400
        assert "1 character" in response.get_json()["error"]

    def test_delete_article_service_error(self):
        author = create_test_account(account_id=10, account_role=AccountRole.AUTHOR)
        self._prepare_user_context(author)
        self.adapter.article_service.delete_article = Mock(return_value="Delete Error")
        response = self.client.delete("/api/articles/1")
        assert response.status_code == 403
        assert response.get_json() == {"error": "Delete Error"}

class TestArticleLegacyContent(ArticleAdapterTestBase):
    def test_api_get_article_legacy_plain_text(self):
        author = create_test_account(account_id=1, account_username="author")
        self.mock_account_repo.get_by_id.return_value = author
        plain_content = "Hello world, this is a legacy article."
        legacy_article = create_test_article(
            article_id=1, article_author_id=1,
            article_content=plain_content
        )
        self.mock_article_repo.get_by_id.return_value = legacy_article

        response = self.client.get("/api/articles/1")
        assert response.status_code == 200
        data = response.get_json()
        parsed = json.loads(data["content"])
        assert parsed[0]["type"] == "paragraph"
        assert parsed[0]["content"][0]["text"] == plain_content

    def test_api_get_article_blocknote_content_passes_through(self):
        author = create_test_account(account_id=1, account_username="author")
        self.mock_account_repo.get_by_id.return_value = author
        bn_content = json.dumps([{"type": "heading", "content": [{"type": "text", "text": "Hi"}]}])
        article = create_test_article(
            article_id=2, article_author_id=1,
            article_content=bn_content
        )
        self.mock_article_repo.get_by_id.return_value = article

        response = self.client.get("/api/articles/2")
        assert response.status_code == 200
        data = response.get_json()
        assert data["content"] == bn_content

class TestArticlePagination(ArticleAdapterTestBase):
    def test_pagination_multiple_pages(self):
        self.mock_article_repo.count_all.return_value = 11
        articles = [create_test_article(article_id=i, article_author_id=1) for i in range(10)]
        self.mock_article_repo.get_paginated.return_value = articles
        self.mock_account_repo.get_by_ids.return_value = [create_test_account(account_id=1)]
        response = self.client.get("/")
        assert response.status_code == 200
        assert b'class="page-link-num' in response.data
        assert b"page-link-num active" in response.data
        assert b"/?page=2" in response.data
        assert response.data.count(b'class="editorial-pagination') == 2
        assert b'class="editorial-pagination top' in response.data

    def test_pagination_exact_single_page(self):
        self.mock_article_repo.count_all.return_value = 10
        articles = [create_test_article(article_id=i, article_author_id=1) for i in range(10)]
        self.mock_article_repo.get_paginated.return_value = articles
        self.mock_account_repo.get_by_ids.return_value = [create_test_account(account_id=1)]
        response = self.client.get("/")
        assert response.status_code == 200
        assert b"pagination-link--hidden" in response.data
        assert response.data.count(b'class="page-link-num') == 2

    def test_pagination_empty_state(self):
        self.mock_article_repo.count_all.return_value = 0
        self.mock_article_repo.get_paginated.return_value = []
        response = self.client.get("/")
        assert response.status_code == 200
        assert b"No articles found in the database." in response.data
        assert b'class="page-link-num' not in response.data

    def test_pagination_truncated_start(self):
        self.mock_article_repo.count_all.return_value = 150
        articles = [create_test_article(article_id=i, article_author_id=1) for i in range(10)]
        self.mock_article_repo.get_paginated.return_value = articles
        self.mock_account_repo.get_by_ids.return_value = [create_test_account(account_id=1)]
        response = self.client.get("/")
        assert response.status_code == 200
        assert b'page=1"' in response.data
        assert b'page=10"' in response.data
        assert b'page=11"' in response.data
        assert b'page=12"' in response.data
        assert b'page=13"' not in response.data
        assert b"..." in response.data
        assert b'page=15"' in response.data

    def test_pagination_truncated_middle(self):
        self.mock_article_repo.count_all.return_value = 1200
        articles = [create_test_article(article_id=i, article_author_id=1) for i in range(10)]
        self.mock_article_repo.get_paginated.return_value = articles
        self.mock_account_repo.get_by_ids.return_value = [create_test_account(account_id=1)]
        response = self.client.get("/?page=50")
        assert response.status_code == 200
        assert b'page=1"' in response.data
        assert b'page=44"' not in response.data
        assert b'page=45"' in response.data
        assert b'page=55"' in response.data
        assert b'page=56"' not in response.data
        assert b'page=120"' in response.data

    def test_pagination_prev_next_visibility_bound(self):
        self.mock_account_repo.get_by_ids.return_value = [create_test_account(account_id=1)]
        articles = [create_test_article(article_id=i, article_author_id=1) for i in range(10)]
        self.mock_article_repo.count_all.return_value = 50
        self.mock_article_repo.get_paginated.return_value = articles
        response = self.client.get("/")
        assert response.data.count(b"pagination-link--hidden") == 2
        response = self.client.get("/?page=3")
        assert response.data.count(b"pagination-link--hidden") == 0
        response = self.client.get("/?page=5")
        assert response.data.count(b"pagination-link--hidden") == 2
