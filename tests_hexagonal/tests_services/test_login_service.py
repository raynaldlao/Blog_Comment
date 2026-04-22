from unittest.mock import MagicMock

from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.services.login_service import LoginService
from tests_hexagonal.exceptions_tests import ExceptionTest
from tests_hexagonal.test_domain_factories import create_test_account


class TestLoginService:
    def setup_method(self):
        self.mock_repo = MagicMock(spec=AccountRepository, autospec=True)
        self.mock_session_repo = MagicMock(spec=AccountSessionRepository, autospec=True)
        self.service = LoginService(
            account_repository=self.mock_repo,
            session_repository=self.mock_session_repo
        )

    def test_authenticate_user_success(self):
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account

        result = self.service.authenticate_user(
            username=fake_account.account_username,
            password=fake_account.account_password
        )

        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        self.mock_session_repo.save_account.assert_called_once_with(fake_account)
        assert result is not None
        assert result.account_username == "leia"

    def test_authenticate_user_wrong_password(self):
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account

        result = self.service.authenticate_user(
            username=fake_account.account_username,
            password="bad_password"
        )

        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        self.mock_session_repo.save_account.assert_not_called()
        assert result is None

    def test_authenticate_user_non_existent(self):
        self.mock_repo.find_by_username.return_value = None
        result = self.service.authenticate_user(username="phantom", password="nothing")
        self.mock_repo.find_by_username.assert_called_once_with("phantom")
        self.mock_session_repo.save_account.assert_not_called()
        assert result is None

    def test_get_current_account(self):
        fake_account = create_test_account()
        self.mock_session_repo.get_account.return_value = fake_account
        result = self.service.get_current_account()
        self.mock_session_repo.get_account.assert_called_once()
        assert result == fake_account

    def test_terminate_session(self):
        self.service.terminate_session()
        self.mock_session_repo.clear.assert_called_once()

    def test_authenticate_user_session_repo_failure(self):
        import pytest
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account
        self.mock_session_repo.save_account.side_effect = ExceptionTest("Storage failure")
        with pytest.raises(ExceptionTest, match="Storage failure"):
            self.service.authenticate_user("leia", "password123")
