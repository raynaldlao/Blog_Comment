from unittest.mock import Mock

from src.application.input_ports.account_session_management import AccountSessionManagement
from src.application.output_ports.account_repository import AccountRepository
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
        self.mock_session = Mock(spec=AccountSessionManagement, autospec=True)

        self.service = LoginService(
            account_repository=self.mock_repo,
            session_service=self.mock_session
        )

        self.adapter = LoginAdapter(login_service=self.service)
        self.app.add_url_rule("/login", view_func=self.adapter.render_login_page, methods=["GET"], endpoint="auth.login")
        self.app.add_url_rule("/login", view_func=self.adapter.authenticate, methods=["POST"], endpoint="auth.login_post")
        self._register_dummy_route("/articles", "article.list_articles", "articles")
        self._register_dummy_route("/register", "registration.register", "reg")

    def test_get_login_page(self):
        response = self.client.get("/login")
        assert response.status_code == 200
        assert b"Welcome Back" in response.data

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
        self.mock_session.start_session.assert_called_once_with(account)

    def test_post_login_invalid_credentials(self):
        self.mock_repo.find_by_username.return_value = None

        response = self.client.post("/login", data={
            "username": "wrong",
            "password": "wrong"
        }, follow_redirects=True)

        assert b"Invalid username or password." in response.data
        self.mock_repo.find_by_username.assert_called_once()
