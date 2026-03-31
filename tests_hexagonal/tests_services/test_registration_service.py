from datetime import datetime
from unittest.mock import MagicMock

from src.application.domain.account import Account, AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.services.registration_service import RegistrationService


def test_create_account_success():
    mock_repo = MagicMock(spec=AccountRepository)
    service = RegistrationService(account_repository=mock_repo)
    mock_repo.find_by_username.return_value = None
    mock_repo.find_by_email.return_value = None

    result = service.create_account(
        username="leia",
        password="password123",
        email="leia@galaxy.com"
    )

    mock_repo.find_by_username.assert_called_once_with("leia")
    mock_repo.find_by_email.assert_called_once_with("leia@galaxy.com")
    mock_repo.save.assert_called_once_with(result)
    assert isinstance(result, Account)
    assert result.account_username == "leia"
    assert result.account_email == "leia@galaxy.com"
    assert result.account_role == AccountRole.USER


def test_create_account_username_taken():
    mock_repo = MagicMock(spec=AccountRepository)
    service = RegistrationService(account_repository=mock_repo)

    existing_account = Account(
        account_id=1,
        account_username="leia",
        account_password="existing_pass",
        account_email="existing@galaxy.com",
        account_role=AccountRole.USER,
        account_created_at=datetime.now(),
    )

    mock_repo.find_by_username.return_value = existing_account

    result = service.create_account(
        username="leia",
        password="password123",
        email="new@galaxy.com"
    )

    mock_repo.find_by_username.assert_called_once_with("leia")
    mock_repo.find_by_email.assert_not_called()
    mock_repo.save.assert_not_called()
    assert result == "This username is already taken."


def test_create_account_email_taken():
    mock_repo = MagicMock(spec=AccountRepository)
    service = RegistrationService(account_repository=mock_repo)

    existing_account = Account(
        account_id=2,
        account_username="han",
        account_password="other_pass",
        account_email="leia@galaxy.com",
        account_role=AccountRole.USER,
        account_created_at=datetime.now(),
    )

    mock_repo.find_by_username.return_value = None
    mock_repo.find_by_email.return_value = existing_account

    result = service.create_account(
        username="new_user",
        password="password123",
        email="leia@galaxy.com"
    )

    mock_repo.find_by_username.assert_called_once_with("new_user")
    mock_repo.find_by_email.assert_called_once_with("leia@galaxy.com")
    mock_repo.save.assert_not_called()
    assert result == "This email is already taken."
