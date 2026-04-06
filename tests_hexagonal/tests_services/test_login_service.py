from unittest.mock import MagicMock

from src.application.output_ports.account_repository import AccountRepository
from src.application.services.login_service import LoginService
from tests_hexagonal.test_domain_factories import create_test_account


class TestLoginService:
    """
    Tests for the LoginService to ensure authentication logic is correct.
    """

    def setup_method(self):
        """
        Setup the test environment by mocking the AccountRepository.
        """
        self.mock_repo = MagicMock(spec=AccountRepository, autospec=True)
        self.service = LoginService(account_repository=self.mock_repo)

    def test_authenticate_user_success(self):
        """
        Ensures that correct credentials return the corresponding account.
        """
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account

        result = self.service.authenticate_user(
            username=fake_account.account_username,
            password=fake_account.account_password
        )

        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        assert result is not None
        assert result.account_username == "leia"

    def test_authenticate_user_wrong_password(self):
        """
        Ensures that incorrect password returns None.
        """
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account

        result = self.service.authenticate_user(
            username=fake_account.account_username,
            password="bad_password"
        )

        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        assert result is None

    def test_authenticate_user_non_existent(self):
        """
        Ensures that non-existent username returns None.
        """
        self.mock_repo.find_by_username.return_value = None

        result = self.service.authenticate_user(username="phantom", password="nothing")

        self.mock_repo.find_by_username.assert_called_once_with("phantom")
        assert result is None
