from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for a login request.

    Validates the data received at the authentication endpoint before
    it is passed to the AccountManagementPort.
    """

    username: str = Field(..., description="The account username.")
    password: str = Field(..., description="The account password.")
