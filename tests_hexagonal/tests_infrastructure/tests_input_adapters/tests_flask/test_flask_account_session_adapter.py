from unittest.mock import Mock

from flask import g as global_request_context

from src.application.domain.account import Account, AccountRole
from src.application.input_ports.account_session_management import AccountSessionManagementPort
from src.infrastructure.input_adapters.flask.flask_account_session_adapter import AccountSessionAdapter
from tests_hexagonal.test_domain_factories import create_test_account
from tests_hexagonal.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class TestAccountSessionAdapter(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_session_service = Mock(spec=AccountSessionManagementPort, autospec=True)
        self.adapter = AccountSessionAdapter(session_service=self.mock_session_service)

        self.app.add_url_rule(
            "/logout",
            view_func=self.adapter.logout,
            endpoint="auth.logout"
        )

        self.app.add_url_rule(
            "/profile",
            view_func=self.adapter.display_profile,
            endpoint="profile.profile"
        )

        self._register_dummy_route("/articles", "article.list_articles", "articles")
        self._register_dummy_route("/login", "auth.login", "login")

    def test_logout_clears_session(self):
        response = self.client.get("/logout", follow_redirects=True)
        assert b"You have been logged out." in response.data
        self.mock_session_service.terminate_session.assert_called_once()

    def test_get_profile_success(self):
        fake_user = create_test_account()
        self.mock_session_service.get_current_account.return_value = fake_user
        response = self.client.get("/profile")
        assert response.status_code == 200
        assert b"leia" in response.data
        assert b"leia@galaxy.com" in response.data
        self.mock_session_service.get_current_account.assert_called_once()

    def test_get_profile_unauthenticated(self):
        self.mock_session_service.get_current_account.return_value = None
        response = self.client.get("/profile", follow_redirects=True)
        assert b"Please sign in to view your profile." in response.data
        assert b"login" in response.data


class TestAccountSessionBeforeRequestHook(FlaskInputAdapterTestBase):
    """
    Tests for the 'before_request' lifecycle hook registered by AccountSessionAdapter.
    Verifies that the current user identity is correctly injected into flask.g
    before every request, for both authenticated and anonymous scenarios.
    """

    def setup_method(self):
        super().setup_method()
        self.mock_session_service = Mock(spec=AccountSessionManagementPort, autospec=True)
        self.adapter = AccountSessionAdapter(session_service=self.mock_session_service)

    def _capture_handler(self, **kwargs):
        """Route handler that captures the current_user from flask.g."""
        self._captured_user = global_request_context.get("current_user")
        return "OK", 200

    def _capture_user_via_route(self, endpoint):
        """Triggers a request on a dummy route to capture the injected user."""
        self.app.add_url_rule(f"/{endpoint}", view_func=self._capture_handler, endpoint=endpoint)
        self.client.get(f"/{endpoint}")
        return self._captured_user

    def test_before_request_injects_authenticated_user(self):
        test_account = create_test_account(account_username="AgentSmith", account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = test_account
        self.adapter.register_before_request_handler(self.app)
        captured_user = self._capture_user_via_route("test-authenticated")
        assert captured_user is not None
        assert isinstance(captured_user, Account)
        assert captured_user.account_username == "AgentSmith"
        assert captured_user.account_role == AccountRole.ADMIN

    def test_before_request_injects_author_user(self):
        test_account = create_test_account(account_username="AuthorWriter", account_role=AccountRole.AUTHOR)
        self.mock_session_service.get_current_account.return_value = test_account
        self.adapter.register_before_request_handler(self.app)
        captured_user = self._capture_user_via_route("test-author")
        assert captured_user is not None
        assert captured_user.account_role == AccountRole.AUTHOR

    def test_before_request_injects_none_when_anonymous(self):
        self.mock_session_service.get_current_account.return_value = None
        self.adapter.register_before_request_handler(self.app)
        captured_user = self._capture_user_via_route("test-anonymous")
        assert captured_user is None

    def test_before_request_isolation_between_requests(self):
        self.app.add_url_rule("/req1", view_func=self._capture_handler, endpoint="req1")
        self.app.add_url_rule("/req2", view_func=self._capture_handler, endpoint="req2")
        admin_account = create_test_account(account_username="Admin", account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = admin_account
        self.adapter.register_before_request_handler(self.app)
        self.client.get("/req1")
        user1 = self._captured_user
        assert user1 is not None and user1.account_username == "Admin"
        self.mock_session_service.get_current_account.return_value = None
        self.client.get("/req2")
        user2 = self._captured_user
        assert user2 is None
