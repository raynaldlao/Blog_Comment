from unittest.mock import Mock

from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.services.account_session_service import AccountSessionService
from src.infrastructure.input_adapters.account_session_adapter import AccountSessionAdapter
from tests_hexagonal.test_domain_factories import create_test_account
from tests_hexagonal.tests_infrastructure.tests_input_adapters.input_adapter_test_utils import (
    FlaskInputAdapterTestBase,
)


class TestAccountSessionAdapter(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_repo = Mock(spec=AccountRepository, autospec=True)
        self.mock_session_repo = Mock(spec=AccountSessionRepository, autospec=True)

        self.service = AccountSessionService(
            session_repository=self.mock_session_repo,
            account_repository=self.mock_repo
        )

        self.adapter = AccountSessionAdapter(session_service=self.service)

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

        self._register_dummy_route("/articles", "article.list_articles", "articles")
        self._register_dummy_route("/login", "auth.login", "login")

    def test_logout_clears_session(self):
        response = self.client.get("/logout", follow_redirects=True)

        assert b"You have been logged out." in response.data
        self.mock_session_repo.invalidate.assert_called_once()

    def test_get_profile_success(self):
        fake_user = create_test_account()
        self.mock_session_repo.retrieve_value.return_value = fake_user.account_id
        self.mock_repo.get_by_id.return_value = fake_user

        response = self.client.get("/profile")

        assert response.status_code == 200
        assert b"leia" in response.data
        assert b"leia@galaxy.com" in response.data

    def test_get_profile_unauthenticated(self):
        self.mock_session_repo.retrieve_value.return_value = None

        response = self.client.get("/profile", follow_redirects=True)

        assert b"Please sign in to view your profile." in response.data
        assert b"login" in response.data
