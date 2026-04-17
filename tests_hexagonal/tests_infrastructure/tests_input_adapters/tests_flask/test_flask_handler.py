from unittest.mock import Mock

from flask import g as global_request_context

from src.application.domain.account import Account, AccountRole
from src.application.input_ports.account_session_management import AccountSessionManagement
from src.infrastructure.input_adapters.flask.flask_handler import FlaskHandler
from tests_hexagonal.test_domain_factories import create_test_account
from tests_hexagonal.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class TestFlaskHandler(FlaskInputAdapterTestBase):
    def setup_method(self) -> None:
        super().setup_method()
        self.mock_session_service = Mock(spec=AccountSessionManagement)
        self._captured_user = "NOT_SET"

    def _capture_handler(self, **kwargs) -> tuple:
        """
        Dedicated route handler for capturing the context state.
        Updates the internal `_captured_user` state with the value from `global_request_context`.

        Args:
            **kwargs: Dynamic URL parameters (unused).

        Returns:
            tuple: A standard Flask response tuple ("OK", 200).
        """
        self._captured_user = global_request_context.get("current_user")
        return "OK", 200

    def _capture_user_via_route(self, endpoint: str) -> Account | None | str:
        """
        Triggers a request on a dummy route to capture the current user from the context.

        Args:
            endpoint (str): The dynamic endpoint name to register and call (e.g., "test-route").

        Returns:
            Account|None|str: The captured user object, None if anonymous, or "NOT_SET" if not captured.
        """
        self.app.add_url_rule(f"/{endpoint}", view_func=self._capture_handler, endpoint=endpoint)
        self.client.get(f"/{endpoint}")
        return self._captured_user

    def test_handler_injects_current_user_into_context(self):
        test_account = create_test_account(account_username="AgentSmith", account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = test_account
        FlaskHandler.register_before_request_handler(self.app, self.mock_session_service)
        captured_user = self._capture_user_via_route("test-authenticated")
        self.mock_session_service.get_current_account.assert_called_once()
        assert captured_user is not None
        assert captured_user.account_username == "AgentSmith"
        assert captured_user.account_role == AccountRole.ADMIN

    def test_handler_injects_none_when_anonymous(self):
        self.mock_session_service.get_current_account.return_value = None
        FlaskHandler.register_before_request_handler(self.app, self.mock_session_service)
        captured_user = self._capture_user_via_route("test-anonymous")
        self.mock_session_service.get_current_account.assert_called_once()
        assert captured_user is None
