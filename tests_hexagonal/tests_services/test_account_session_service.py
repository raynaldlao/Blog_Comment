from unittest.mock import Mock

from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.services.account_session_service import AccountSessionService
from tests_hexagonal.test_domain_factories import create_test_account


class TestAccountSessionService:
    def setup_method(self):
        self.session_repo = Mock(spec=AccountSessionRepository)
        self.account_repo = Mock(spec=AccountRepository)
        self.service = AccountSessionService(
            session_repository=self.session_repo,
            account_repository=self.account_repo
        )

    def test_start_session(self):
        account = create_test_account()
        self.service.start_session(account)
        self.session_repo.set.assert_any_call("user_id", account.account_id)
        self.session_repo.set.assert_any_call("username", account.account_username)
        self.session_repo.set.assert_any_call("role", account.account_role.value)

    def test_get_current_account_success(self):
        account = create_test_account()
        self.session_repo.get.return_value = account.account_id
        self.account_repo.get_by_id.return_value = account
        result = self.service.get_current_account()
        assert result is not None
        assert result.account_id == account.account_id
        self.account_repo.get_by_id.assert_called_once_with(account.account_id)

    def test_get_current_account_no_session(self):
        self.session_repo.get.return_value = None
        result = self.service.get_current_account()
        assert result is None

    def test_terminate_session(self):
        self.service.terminate_session()
        self.session_repo.clear.assert_called_once()
