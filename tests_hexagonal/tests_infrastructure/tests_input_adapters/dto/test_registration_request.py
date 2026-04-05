import pytest
from pydantic import ValidationError

from src.infrastructure.input_adapters.dto.registration_request import RegistrationRequest


def test_registration_request_valid():
    request = RegistrationRequest(
        username="testuser",
        email="test@example.com",
        password="password123",
        confirm_password="password123",
    )
    assert request.username == "testuser"
    assert str(request.email) == "test@example.com"
    assert request.password == "password123"


def test_registration_request_invalid_email():
    with pytest.raises(ValidationError) as exc_info:
        RegistrationRequest(
            username="testuser",
            email="not-an-email",
            password="password123",
            confirm_password="password123",
        )
    assert "value is not a valid email address" in str(exc_info.value)


def test_registration_request_passwords_do_not_match():
    with pytest.raises(ValidationError) as exc_info:
        RegistrationRequest(
            username="testuser",
            email="test@example.com",
            password="password123",
            confirm_password="differentpassword",
        )
    assert "Passwords do not match." in str(exc_info.value)
