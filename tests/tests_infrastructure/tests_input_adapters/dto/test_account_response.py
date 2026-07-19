from datetime import datetime

from src.application.domain.account import AccountRole
from src.infrastructure.input_adapters.dto.account_response import AccountResponse
from tests.test_domain_factories import create_test_account


def test_account_response_creation():
    fixed_date = datetime(2026, 4, 7, 10, 0, 0)

    response = AccountResponse(
        account_id=1,
        account_username="leia",
        account_email="leia@galaxy.com",
        account_role="user",
        account_created_at=fixed_date
    )

    assert response.account_id == 1
    assert response.account_username == "leia"
    assert response.account_role == "user"
    assert response.account_created_at == fixed_date


def test_from_domain():
    fixed_date = datetime(2026, 4, 7, 10, 0, 0)

    domain_account = create_test_account(
        account_id=1,
        account_username="leia",
        account_email="leia@galaxy.com",
        account_role=AccountRole.USER,
        account_created_at=fixed_date
    )

    response = AccountResponse.from_domain(domain_account)
    assert response.account_id == 1
    assert response.account_username == "leia"
    assert response.account_email == "leia@galaxy.com"
    assert response.account_role == "user"
    assert response.account_created_at == fixed_date
    assert not hasattr(response, "account_password")
    assert not hasattr(response, "password")
    response_dict = response.model_dump()
    assert "account_password" not in response_dict
    assert "password" not in response_dict


def test_from_domain_with_banned_true():
    fixed_date = datetime(2026, 4, 7, 10, 0, 0)

    domain_account = create_test_account(
        account_id=1,
        account_username="leia",
        account_email="leia@galaxy.com",
        account_role=AccountRole.USER,
        account_created_at=fixed_date,
        is_banned=True,
        ban_reason="Spam",
    )

    response = AccountResponse.from_domain(domain_account)
    assert response.is_banned is True
    assert response.ban_reason == "Spam"


def test_from_domain_with_banned_false():
    fixed_date = datetime(2026, 4, 7, 10, 0, 0)

    domain_account = create_test_account(
        account_id=1,
        account_username="leia",
        account_email="leia@galaxy.com",
        account_role=AccountRole.USER,
        account_created_at=fixed_date,
    )

    response = AccountResponse.from_domain(domain_account)
    assert response.is_banned is False
    assert response.ban_reason is None
