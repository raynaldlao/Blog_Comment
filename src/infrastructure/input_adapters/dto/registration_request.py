import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from blog_exceptions import PasswordsDoNotMatchError, WeakPasswordError


class RegistrationRequest(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for an account registration request.

    Validates the data received at the registration endpoint before
    it is passed to the RegistrationManagementPort. Enforces strict rules
    on username format (3-30 chars, alphanumeric + underscores/hyphens),
    email format, password strength (8+ chars, lowercase, uppercase,
    special character), and password confirmation.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="The desired username. 3-30 characters: letters, numbers, underscores, hyphens.",
    )
    email: EmailStr = Field(..., description="A valid email address.")
    password: str = Field(
        ...,
        min_length=8,
        description="The account password. Must contain at least one uppercase, one lowercase, and one special character.",
    )
    confirm_password: str = Field(..., description="Must match the password field.")

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
            raise WeakPasswordError("Le mot de passe doit contenir au moins une minuscule.")
        if not re.search(r"[A-Z]", v):
            raise WeakPasswordError("Le mot de passe doit contenir au moins une majuscule.")
        if not re.search(r"[^a-zA-Z0-9]", v):
            raise WeakPasswordError("Le mot de passe doit contenir au moins un caractère spécial.")
        return v

    @model_validator(mode="after")
    def passwords_must_match(self) -> "RegistrationRequest":
        """
        Cross-field validator that ensures 'password' and 'confirm_password' are identical.

        Returns:
            RegistrationRequest: The validated model instance.

        Raises:
            PasswordsDoNotMatchError: If 'password' and 'confirm_password' do not match.
        """
        if self.password != self.confirm_password:
            raise PasswordsDoNotMatchError("Les mots de passe ne correspondent pas.")
        return self
