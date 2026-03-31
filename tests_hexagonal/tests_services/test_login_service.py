from datetime import datetime
from unittest.mock import MagicMock

from src.application.domain.account import Account, AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.services.login_service import LoginService


def test_authenticate_user_success():
    mock_repo = MagicMock(spec=AccountRepository)
    login_service = LoginService(account_repository=mock_repo)

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role=AccountRole.USER,
        account_created_at=datetime.now()
    )

    mock_repo.find_by_username.return_value = fake_account
    result = login_service.authenticate_user(username="leia", password="password123")
    mock_repo.find_by_username.assert_called_once_with("leia")
    assert result is not None
    assert result.account_username == "leia"


def test_authenticate_user_wrong_password():
    mock_repo = MagicMock(spec=AccountRepository)
    login_service = LoginService(account_repository=mock_repo)

    fake_account = Account(
        account_id=1,
        account_username="leia",
        account_password="password123",
        account_email="leia@galaxy.com",
        account_role=AccountRole.USER,
        account_created_at=datetime.now()
    )

    mock_repo.find_by_username.return_value = fake_account
    result = login_service.authenticate_user(username="leia", password="bad_password")
    mock_repo.find_by_username.assert_called_once_with("leia")
    assert result is None


def test_authenticate_user_non_existent():
    mock_repo = MagicMock(spec=AccountRepository)
    login_service = LoginService(account_repository=mock_repo)
    mock_repo.find_by_username.return_value = None
    result = login_service.authenticate_user(username="phantom", password="nothing")
    mock_repo.find_by_username.assert_called_once_with("phantom")
    assert result is None
