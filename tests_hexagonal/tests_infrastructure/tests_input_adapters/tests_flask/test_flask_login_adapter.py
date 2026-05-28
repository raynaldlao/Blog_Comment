from unittest.mock import Mock

from src.application.domain.account import AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.output_ports.password_hasher_repository import PasswordHasherRepository
from src.application.services.login_service import LoginService
from src.infrastructure.input_adapters.flask.flask_login_adapter import LoginAdapter
from tests_hexagonal.test_domain_factories import create_test_account
from tests_hexagonal.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class TestLoginAdapter(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_repo = Mock(spec=AccountRepository, autospec=True)
        self.mock_session_repo = Mock(spec=AccountSessionRepository, autospec=True)
        self.mock_hasher = Mock(spec=PasswordHasherRepository, autospec=True)
        self.mock_hasher.verify.return_value = True
        self.mock_hasher.check_needs_rehash.return_value = False

        self.service = LoginService(
            account_repository=self.mock_repo,
            session_repository=self.mock_session_repo,
            password_hasher_repository=self.mock_hasher
        )

        self.adapter = LoginAdapter(login_service=self.service)
        self.app.add_url_rule("/login", view_func=self.adapter.render_login_page, methods=["GET"], endpoint="auth.login")
        self.app.add_url_rule("/login", view_func=self.adapter.authenticate, methods=["POST"], endpoint="auth.login_post")
        self._register_dummy_route("/articles", "article.list_articles", "articles")
        self._register_dummy_route("/register", "registration.register", "reg")
        self._register_dummy_route("/profile", "auth.profile", "profile")
        self._register_dummy_route("/logout", "auth.logout", "logout")
        self._register_dummy_route("/articles/new", "article.render_create_page", "new_article")

    def test_get_login_page(self):
        response = self.client.get("/login")
        assert response.status_code == 200
        assert b"Welcome Back" in response.data

    def test_get_login_page_authenticated(self):
        user = create_test_account()
        self.set_current_user(user)
        response = self.client.get("/login")
        assert response.status_code == 200
        assert b"Welcome Back" in response.data
        assert b"Profile" in response.data
        assert b"Logout" in response.data

    def test_get_login_page_authenticated_author(self):
        author = create_test_account(account_role=AccountRole.AUTHOR)
        self.set_current_user(author)
        response = self.client.get("/login")
        assert response.status_code == 200
        assert b"New article" in response.data

    def test_post_login_success(self):
        account = create_test_account()
        self.mock_repo.find_by_username.return_value = account

        response = self.client.post("/login", data={
            "username": "leia",
            "password": "password123"
        })

        assert response.status_code == 302
        assert response.location.endswith("/articles")
        self.mock_repo.find_by_username.assert_called_once_with("leia")
        self.mock_session_repo.save_account.assert_called_once_with(account)

    def test_post_login_invalid_credentials(self):
        self.mock_repo.find_by_username.return_value = None

        response = self.client.post("/login", data={
            "username": "wrong",
            "password": "wrong"
        }, follow_redirects=True)

        assert b"Invalid username or password." in response.data
        assert b"alert-error" in response.data
        self.mock_repo.find_by_username.assert_called_once()
        self.mock_session_repo.save_account.assert_not_called()

    def test_post_login_validation_error(self):
        response = self.client.post("/login", data={"username": ""}, follow_redirects=True)
        assert b"Validation Error" in response.data or b"field required" in response.data.lower()
        assert b"alert-error" in response.data
