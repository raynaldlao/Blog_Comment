from unittest.mock import MagicMock

from src.application.domain.account import Account, AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.services.registration_service import RegistrationService
from tests_hexagonal.test_domain_factories import create_test_account


class TestRegistrationService:
    def setup_method(self):
        self.mock_repo = MagicMock(spec=AccountRepository, autospec=True)
        self.service = RegistrationService(account_repository=self.mock_repo)

    def test_create_account_success(self):
        self.mock_repo.find_by_username.return_value = None
        self.mock_repo.find_by_email.return_value = None

        result = self.service.create_account(
            username="leia",
            password="password123",
            email="leia@galaxy.com"
        )

        self.mock_repo.find_by_username.assert_called_once_with("leia")
        self.mock_repo.find_by_email.assert_called_once_with("leia@galaxy.com")
        self.mock_repo.save.assert_called_once_with(result)
        assert isinstance(result, Account)
        assert result.account_username == "leia"
        assert result.account_email == "leia@galaxy.com"
        assert result.account_role == AccountRole.USER

    def test_create_account_username_taken(self):
        existing_account = create_test_account(
            account_id=1,
            account_username="leia",
            account_email="existing@galaxy.com"
        )

        self.mock_repo.find_by_username.return_value = existing_account

        result = self.service.create_account(
            username="leia",
            password="password123",
            email="new@galaxy.com"
        )

        self.mock_repo.find_by_username.assert_called_once_with("leia")
        self.mock_repo.find_by_email.assert_not_called()
        self.mock_repo.save.assert_not_called()
        assert result == "This username is already taken."

    def test_create_account_email_taken(self):
        existing_account = create_test_account(
            account_id=2,
            account_username="han",
            account_email="leia@galaxy.com"
        )

        self.mock_repo.find_by_username.return_value = None
        self.mock_repo.find_by_email.return_value = existing_account

        result = self.service.create_account(
            username="new_user",
            password="password123",
            email="leia@galaxy.com"
        )

        self.mock_repo.find_by_username.assert_called_once_with("new_user")
        self.mock_repo.find_by_email.assert_called_once_with("leia@galaxy.com")
        self.mock_repo.save.assert_not_called()
        assert result == "This email is already taken."
