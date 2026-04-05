from datetime import datetime

from src.application.domain.account import Account, AccountRole
from src.infrastructure.input_adapters.dto.account_response import AccountResponse


def test_account_response_from_domain_excludes_password():
    """
    Test that mapping from an Account domain entity correctly populates
    all public fields and completely excludes the password.
    """
    domain_account = Account(
        account_id=1,
        account_username="testuser",
        account_password="secret_password_123",
        account_email="test@example.com",
        account_role=AccountRole.USER,
        account_created_at=datetime(2023, 1, 1, 12, 0, 0),
    )

    response_dto = AccountResponse.from_domain(domain_account)
    assert response_dto.account_id == 1
    assert response_dto.account_username == "testuser"
    assert response_dto.account_email == "test@example.com"
    assert response_dto.account_role == "user"
    assert response_dto.account_created_at == datetime(2023, 1, 1, 12, 0, 0)
    assert not hasattr(response_dto, "account_password")
    assert not hasattr(response_dto, "password")
    response_dict = response_dto.model_dump()
    assert "account_password" not in response_dict
    assert "password" not in response_dict
