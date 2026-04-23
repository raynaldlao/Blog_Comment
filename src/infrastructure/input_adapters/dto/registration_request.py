from pydantic import BaseModel, EmailStr, Field, model_validator


class RegistrationRequest(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for an account registration request.

    Validates the data received at the registration endpoint before
    it is passed to the RegistrationManagementPort. Enforces strict rules
    on email format, password length, and password confirmation.
    """

    username: str = Field(..., description="The desired username.")
    email: EmailStr = Field(..., description="A valid email address.")
    password: str = Field(..., description="The account password.")
    confirm_password: str = Field(..., description="Must match the password field.")

    @model_validator(mode="after")
    def passwords_must_match(self) -> "RegistrationRequest":
        """
        Cross-field validator that ensures 'password' and 'confirm_password' are identical.

        Returns:
            RegistrationRequest: The validated model instance.

        Raises:
            ValueError: If 'password' and 'confirm_password' do not match.
        """
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self
