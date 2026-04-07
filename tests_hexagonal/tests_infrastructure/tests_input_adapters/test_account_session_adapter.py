import os
from unittest.mock import Mock

from flask import Flask, get_flashed_messages

from src.application.input_ports.account_session_management import AccountSessionManagement
from src.infrastructure.input_adapters.account_session_adapter import AccountSessionAdapter
from tests_hexagonal.test_domain_factories import create_test_account


class TestAccountSessionAdapter:
    def setup_method(self):
        template_dir = os.path.abspath("src/infrastructure/input_adapters/templates")
        self.app = Flask(__name__, template_folder=template_dir)
        self.app.config["SECRET_KEY"] = "test_secret"
        self.app.config["SERVER_NAME"] = "localhost"
        self.app.config["TESTING"] = True
        self.mock_service = Mock(spec=AccountSessionManagement)
        self.adapter = AccountSessionAdapter(session_service=self.mock_service)

        self.app.add_url_rule(
            "/logout",
            view_func=self.adapter.logout,
            endpoint="logout.logout"
        )

        self.app.add_url_rule(
            "/profile",
            view_func=self.adapter.display_profile,
            endpoint="account_session.profile"
        )

        @self.app.route("/articles")
        def articles_dummy():
            return f"articles {get_flashed_messages()}"
        self.app.add_url_rule("/articles", endpoint="article.list_articles")

        @self.app.route("/login")
        def login_dummy():
            return f"login {get_flashed_messages()}"
        self.app.add_url_rule("/login", endpoint="auth.login")

    def test_logout_clears_session(self):
        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.get("/logout", follow_redirects=True)

                assert b"You have been logged out." in response.data
                self.mock_service.terminate_session.assert_called_once()

    def test_get_profile_success(self):
        fake_user = create_test_account()
        self.mock_service.get_current_account.return_value = fake_user

        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.get("/profile")

                assert response.status_code == 200
                assert b"leia" in response.data
                assert b"leia@galaxy.com" in response.data

    def test_get_profile_unauthenticated(self):
        self.mock_service.get_current_account.return_value = None

        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.get("/profile", follow_redirects=True)

                assert b"Please sign in to view your profile." in response.data
                assert b"login" in response.data
