import pytest
from pydantic import ValidationError

from src.infrastructure.input_adapters.dto.login_request import LoginRequest


class TestLoginRequest:
    """
    Unit tests for LoginRequest DTO.
    Ensures that validation rules are correctly applied at the boundary.
    """

    def test_login_request_valid(self):
        req = LoginRequest(username="leia", password="password123")
        assert req.username == "leia"
        assert req.password == "password123"

    def test_login_request_missing_username(self):
        with pytest.raises(ValidationError):
            LoginRequest(password="password123")

    def test_login_request_missing_password(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="leia")
