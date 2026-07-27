import re

from flask_babel import gettext as _
from pydantic import BaseModel, Field, field_validator

from blog_exceptions import WeakPasswordError


class UpdatePasswordRequest(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for a password update request.

    Validates the new password at the web boundary before it is passed
    to the AccountSessionManagementPort. Enforces minimum length and
    character class requirements (lowercase, uppercase, special).
    """

    password: str = Field(
        ...,
        min_length=8,
        description=(
            "The new password. Minimum 8 characters, must contain at least "
            "one lowercase, one uppercase, and one special character."
        ),
    )

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        Validates password strength using three regex checks.

        Ensures the password contains at least one lowercase letter,
        one uppercase letter, and one special character.

        Args:
            v: The password string to validate.

        Returns:
            str: The validated password if all checks pass.

        Raises:
            WeakPasswordError: If any strength requirement is not met.
        """
        if not re.search(r"[a-z]", v):
            raise WeakPasswordError(
                _("Password must contain at least one lowercase letter.")
            )
        if not re.search(r"[A-Z]", v):
            raise WeakPasswordError(
                _("Password must contain at least one uppercase letter.")
            )
        if not re.search(r"[^a-zA-Z0-9]", v):
            raise WeakPasswordError(
                _("Password must contain at least one special character.")
            )
        return v
