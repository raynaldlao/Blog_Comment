from unittest.mock import Mock

from src.application.input_ports.login_management import LoginManagementPort
from src.infrastructure.input_adapters.login_adapter import LoginAdapter
from tests_hexagonal.test_domain_factories import create_test_account
from tests_hexagonal.tests_infrastructure.tests_input_adapters.input_adapter_test_utils import (
    FlaskInputAdapterTestBase,
)


class TestLoginAdapter(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_service = Mock(spec=LoginManagementPort)
        self.adapter = LoginAdapter(login_service=self.mock_service)
        self.app.add_url_rule("/login", view_func=self.adapter.render_login_page, methods=["GET"], endpoint="auth.login")
        self.app.add_url_rule("/login", view_func=self.adapter.authenticate, methods=["POST"], endpoint="auth.login_post")
        self._register_dummy_route("/articles", "article.list_articles", "articles")
        self._register_dummy_route("/register", "registration.register", "reg")

    def test_get_login_page(self):
        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.get("/login")
                assert response.status_code == 200
                assert b"Welcome Back" in response.data

    def test_post_login_success(self):
        account = create_test_account()
        self.mock_service.authenticate_user.return_value = account

        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.post("/login", data={
                    "username": "leia",
                    "password": "force_is_with_her"
                })

                assert response.status_code == 302
                assert response.location.endswith("/articles")
                self.mock_service.authenticate_user.assert_called_once_with(
                    username="leia",
                    password="force_is_with_her"
                )

    def test_post_login_invalid_credentials(self):
        self.mock_service.authenticate_user.return_value = None
        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.post("/login", data={
                    "username": "wrong",
                    "password": "wrong"
                }, follow_redirects=True)

                assert b"Invalid username or password." in response.data
                self.mock_service.authenticate_user.assert_called_once()
