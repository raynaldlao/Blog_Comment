import pytest
from pydantic import ValidationError

from src.infrastructure.input_adapters.dto.login_request import LoginRequest


def test_login_request_valid():
    request = LoginRequest(username="testuser", password="password123")
    assert request.username == "testuser"
    assert request.password == "password123"


def test_login_request_missing_fields():
    with pytest.raises(ValidationError):
        LoginRequest(username="testuser")
