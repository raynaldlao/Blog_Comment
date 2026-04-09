from unittest.mock import Mock

import pytest
from flask import Flask
from flask import g as global_request_context

from src.application.domain.account import AccountRole
from src.application.input_ports.account_session_management import AccountSessionManagement
from src.infrastructure.input_adapters.flask.flask_handler import FlaskHandler
from tests_hexagonal.test_domain_factories import create_test_account


class TestFlaskHandler:
    @pytest.fixture
    def app(self):
        application = Flask(__name__)
        application.config["TESTING"] = True
        return application

    def test_handler_injects_current_user_into_context(self, app: Flask):
        mock_session_service = Mock(spec=AccountSessionManagement)
        test_account = create_test_account(account_username="AgentSmith", account_role=AccountRole.ADMIN)
        mock_session_service.get_current_account.return_value = test_account
        FlaskHandler.register_before_request_handler(app, mock_session_service)
        captured_user = None

        @app.route("/dummy-test-route")
        def dummy_route():
            nonlocal captured_user
            captured_user = global_request_context.get("current_user")
            return "OK", 200

        with app.test_client() as client:
            response = client.get("/dummy-test-route")

        assert response.status_code == 200
        mock_session_service.get_current_account.assert_called_once()
        assert captured_user is not None
        assert captured_user.account_username == "AgentSmith"
        assert captured_user.account_role == AccountRole.ADMIN

    def test_handler_injects_none_when_anonymous(self, app: Flask):
        mock_session_service = Mock(spec=AccountSessionManagement)
        mock_session_service.get_current_account.return_value = None
        FlaskHandler.register_before_request_handler(app, mock_session_service)
        captured_user = "NOT_NONE"

        @app.route("/dummy-test-route-anon")
        def dummy_route():
            nonlocal captured_user
            captured_user = global_request_context.get("current_user")
            return "OK", 200

        with app.test_client() as client:
            client.get("/dummy-test-route-anon")

        mock_session_service.get_current_account.assert_called_once()
        assert captured_user is None
