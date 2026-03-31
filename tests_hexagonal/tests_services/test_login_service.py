from datetime import datetime
from unittest.mock import MagicMock

from src.application.domain.account import Account, AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.services.login_service import LoginService


class LoginServiceTestBase:
    def setup_method(self):
        self.mock_repo = MagicMock(spec=AccountRepository)
        self.service = LoginService(account_repository=self.mock_repo)


class TestAuthenticateUser(LoginServiceTestBase):
    def test_authenticate_user_success(self):
        fake_account = Account(
            account_id=1,
            account_username="leia",
            account_password="password123",
            account_email="leia@galaxy.com",
            account_role=AccountRole.USER,
            account_created_at=datetime.now()
        )

        self.mock_repo.find_by_username.return_value = fake_account
        result = self.service.authenticate_user(username=fake_account.account_username, password=fake_account.account_password)
        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        assert result is not None
        assert result.account_username == "leia"

    def test_authenticate_user_wrong_password(self):
        fake_account = Account(
            account_id=1,
            account_username="leia",
            account_password="password123",
            account_email="leia@galaxy.com",
            account_role=AccountRole.USER,
            account_created_at=datetime.now()
        )

        self.mock_repo.find_by_username.return_value = fake_account
        result = self.service.authenticate_user(username=fake_account.account_username, password="bad_password")
        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        assert result is None

    def test_authenticate_user_non_existent(self):
        self.mock_repo.find_by_username.return_value = None
        result = self.service.authenticate_user(username="phantom", password="nothing")
        self.mock_repo.find_by_username.assert_called_once_with("phantom")
        assert result is None
