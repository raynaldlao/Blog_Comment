import pytest
from pydantic import ValidationError

from src.infrastructure.input_adapters.dto.registration_request import RegistrationRequest


class TestRegistrationRequest:
    """
    Unit tests for RegistrationRequest DTO.
    Ensures that validation rules (Email, Password matching) are correctly applied.
    """

    def test_registration_request_valid(self):
        req = RegistrationRequest(
            username="leia",
            email="leia@rebels.com",
            password="password123",
            confirm_password="password123"
        )
        assert req.username == "leia"
        assert req.email == "leia@rebels.com"

    def test_registration_request_invalid_email(self):
        with pytest.raises(ValidationError):
            RegistrationRequest(
                username="leia",
                email="invalid-email",
                password="password123",
                confirm_password="password123"
            )

    def test_registration_request_password_mismatch(self):
        with pytest.raises(ValidationError) as excinfo:
            RegistrationRequest(
                username="leia",
                email="leia@rebels.com",
                password="password123",
                confirm_password="different_password"
            )
        assert "Passwords do not match." in str(excinfo.value)

    def test_registration_request_missing_field(self):
        with pytest.raises(ValidationError):
            RegistrationRequest.model_validate({
                "email": "leia@rebels.com",
                "password": "password123",
                "confirm_password": "password123"
            })
