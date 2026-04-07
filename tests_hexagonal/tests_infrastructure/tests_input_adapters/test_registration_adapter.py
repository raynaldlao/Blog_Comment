from unittest.mock import Mock

from flask import Flask

from src.application.input_ports.registration_management import RegistrationManagementPort
from src.infrastructure.input_adapters.registration_adapter import RegistrationAdapter
from tests_hexagonal.test_domain_factories import create_test_account


class TestRegistrationAdapter:
    """
    Tests for the RegistrationAdapter to ensure correct registration flow.
    """

    def setup_method(self):
        import os
        template_dir = os.path.abspath("src/infrastructure/input_adapters/templates")

        self.app = Flask(__name__, template_folder=template_dir)
        self.app.config["SECRET_KEY"] = "test_secret"
        self.app.config["SERVER_NAME"] = "localhost"
        self.app.config["TESTING"] = True
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self.mock_service = Mock(spec=RegistrationManagementPort)
        self.adapter = RegistrationAdapter(registration_service=self.mock_service)
        self.app.add_url_rule("/register", view_func=self.adapter.render_registration_page, methods=["GET"], endpoint="registration.register")
        self.app.add_url_rule("/register", view_func=self.adapter.register, methods=["POST"], endpoint="registration.register_post")

        @self.app.route("/login")
        def login_dummy():
            from flask import get_flashed_messages
            return f"login_page {get_flashed_messages()}"
        self.app.add_url_rule("/login", endpoint="auth.login")

    def test_get_registration_page(self):
        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.get("/register")
                assert response.status_code == 200
                assert b"Join the Blog" in response.data

    def test_post_registration_success(self):
        fake_account = create_test_account()
        self.mock_service.create_account.return_value = fake_account
        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.post("/register", data={
                    "username": "leia",
                    "email": "leia@rebels.com",
                    "password": "password123",
                    "confirm_password": "password123"
                }, follow_redirects=True)

                assert b"Registration successful. Please sign in." in response.data
                assert response.request.path == "/login"
                self.mock_service.create_account.assert_called_once()

    def test_post_registration_password_mismatch(self):
        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.post("/register", data={
                    "username": "leia",
                    "email": "leia@rebels.com",
                    "password": "password123",
                    "confirm_password": "wrong_confirm"
                }, follow_redirects=True)

                assert b"Passwords do not match." in response.data
                self.mock_service.create_account.assert_not_called()

    def test_post_registration_email_taken(self):
        self.mock_service.create_account.return_value = "This email is already taken."
        with self.app.test_request_context():
            with self.app.test_client() as client:
                response = client.post("/register", data={
                    "username": "leia",
                    "email": "leia@rebels.com",
                    "password": "password123",
                    "confirm_password": "password123"
                }, follow_redirects=True)

                assert b"This email is already taken." in response.data
                self.mock_service.create_account.assert_called_once()
