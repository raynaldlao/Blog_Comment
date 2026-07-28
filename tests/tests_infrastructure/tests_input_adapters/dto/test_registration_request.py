import pytest
from pydantic import ValidationError

from src.infrastructure.input_adapters.dto.registration_request import RegistrationRequest

VALID_PASSWORD = "Password1!"


class TestRegistrationRequest:
    """
    Unit tests for RegistrationRequest DTO.
    Ensures that validation rules (Email, Password matching) are correctly applied.
    """

    def test_registration_request_valid(self):
        req = RegistrationRequest(
            username="leia",
            email="leia@rebels.com",
            password=VALID_PASSWORD,
            confirm_password=VALID_PASSWORD,
        )
        assert req.username == "leia"
        assert req.email == "leia@rebels.com"

    def test_registration_request_invalid_email(self):
        with pytest.raises(ValidationError):
            RegistrationRequest(
                username="leia",
                email="invalid-email",
                password=VALID_PASSWORD,
                confirm_password=VALID_PASSWORD,
            )

    def test_registration_request_password_mismatch(self):
        with pytest.raises(ValidationError) as excinfo:
            RegistrationRequest(
                username="leia",
                email="leia@rebels.com",
                password=VALID_PASSWORD,
                confirm_password="Different1!",
            )
        assert "Passwords do not match." in str(excinfo.value)

    def test_registration_request_missing_field(self):
        with pytest.raises(ValidationError):
            RegistrationRequest.model_validate({
                "email": "leia@rebels.com",
                "password": VALID_PASSWORD,
                "confirm_password": VALID_PASSWORD,
            })

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            RegistrationRequest(
                username="ab",
                email="leia@rebels.com",
                password=VALID_PASSWORD,
                confirm_password=VALID_PASSWORD,
            )

    def test_username_invalid_chars(self):
        with pytest.raises(ValidationError):
            RegistrationRequest(
                username="user name!",
                email="leia@rebels.com",
                password=VALID_PASSWORD,
                confirm_password=VALID_PASSWORD,
            )

    def test_password_no_uppercase(self):
        with pytest.raises(ValidationError) as excinfo:
            RegistrationRequest(
                username="leia",
                email="leia@rebels.com",
                password="abcdef8!",
                confirm_password="abcdef8!",
            )
        assert "uppercase" in str(excinfo.value)

    def test_password_no_lowercase(self):
        with pytest.raises(ValidationError) as excinfo:
            RegistrationRequest(
                username="leia",
                email="leia@rebels.com",
                password="ABCDEF8!",
                confirm_password="ABCDEF8!",
            )
        assert "lowercase" in str(excinfo.value)

    def test_password_no_special(self):
        with pytest.raises(ValidationError) as excinfo:
            RegistrationRequest(
                username="leia",
                email="leia@rebels.com",
                password="Abcdefg8",
                confirm_password="Abcdefg8",
            )
        assert "special" in str(excinfo.value)
