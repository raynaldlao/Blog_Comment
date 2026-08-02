import pytest
from pydantic import ValidationError

from src.infrastructure.input_adapters.dto.update_password_request import UpdatePasswordRequest


class TestUpdatePasswordRequest:
    """
    Unit tests for UpdatePasswordRequest DTO.

    Ensures that password validation rules (min_length, lowercase, uppercase,
    special character) are correctly applied at the web boundary.
    """

    def test_valid(self):
        req = UpdatePasswordRequest(password="Pass_Valid1!")
        assert req.password == "Pass_Valid1!"

    def test_no_lowercase(self):
        with pytest.raises(ValidationError) as excinfo:
            UpdatePasswordRequest(password="ALL_UPPER_1!")
        assert "lowercase" in str(excinfo.value)

    def test_no_uppercase(self):
        with pytest.raises(ValidationError) as excinfo:
            UpdatePasswordRequest(password="no_upper_1!")
        assert "uppercase" in str(excinfo.value)

    def test_no_special(self):
        with pytest.raises(ValidationError) as excinfo:
            UpdatePasswordRequest(password="NoSpecial1")
        assert "special" in str(excinfo.value)

    def test_too_short(self):
        with pytest.raises(ValidationError):
            UpdatePasswordRequest(password="Ab_1")

    def test_empty(self):
        with pytest.raises(ValidationError):
            UpdatePasswordRequest(password="")
