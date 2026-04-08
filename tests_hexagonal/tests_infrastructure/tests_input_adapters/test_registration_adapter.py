from unittest.mock import Mock

from src.application.output_ports.account_repository import AccountRepository
from src.application.services.registration_service import RegistrationService
from src.infrastructure.input_adapters.registration_adapter import RegistrationAdapter
from tests_hexagonal.test_domain_factories import create_test_account
from tests_hexagonal.tests_infrastructure.tests_input_adapters.input_adapter_test_utils import (
    FlaskInputAdapterTestBase,
)


class TestRegistrationAdapter(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_repo = Mock(spec=AccountRepository, autospec=True)
        self.service = RegistrationService(account_repository=self.mock_repo)
        self.adapter = RegistrationAdapter(registration_service=self.service)

        self.app.add_url_rule(
            "/register",
            view_func=self.adapter.render_registration_page,
            methods=["GET"],
            endpoint="registration.register"
        )

        self.app.add_url_rule(
            "/register",
            view_func=self.adapter.register,
            methods=["POST"],
            endpoint="registration.register_post"
        )

        self._register_dummy_route("/login", "auth.login", "login_page")

    def test_get_registration_page(self):
        response = self.client.get("/register")
        assert response.status_code == 200
        assert b"Join the Blog" in response.data

    def test_post_registration_success(self):
        self.mock_repo.find_by_username.return_value = None
        self.mock_repo.find_by_email.return_value = None

        response = self.client.post("/register", data={
            "username": "leia",
            "email": "leia@rebels.com",
            "password": "password123",
            "confirm_password": "password123"
        }, follow_redirects=True)

        assert b"Registration successful. Please sign in." in response.data
        assert response.request.path == "/login"
        self.mock_repo.save.assert_called_once()

    def test_post_registration_password_mismatch(self):
        response = self.client.post("/register", data={
            "username": "leia",
            "email": "leia@rebels.com",
            "password": "password123",
            "confirm_password": "wrong_confirm"
        }, follow_redirects=True)

        assert b"Passwords do not match." in response.data
        self.mock_repo.save.assert_not_called()

    def test_post_registration_email_taken(self):
        existing_account = create_test_account(account_email="leia@rebels.com")
        self.mock_repo.find_by_username.return_value = None
        self.mock_repo.find_by_email.return_value = existing_account

        response = self.client.post("/register", data={
            "username": "leia",
            "email": "leia@rebels.com",
            "password": "password123",
            "confirm_password": "password123"
        }, follow_redirects=True)

        assert b"This email is already taken." in response.data
        self.mock_repo.save.assert_not_called()
