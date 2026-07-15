from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.application.domain.account import Account


class AccountResponse(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for account Web responses.

    This class securely exposes account information to the client,
    intentionally omitting the password field. It also includes the
    optional avatar file reference for profile display.
    """

    model_config = ConfigDict(from_attributes=True)

    account_id: int
    account_username: str
    account_email: str
    account_role: str
    account_created_at: datetime | None
    avatar_file_id: str | None = None

    @classmethod
    def from_domain(cls, account: Account) -> "AccountResponse":
        """
        Maps a domain Account entity to a secure AccountResponse DTO.

        Args:
            account (Account): The domain entity.

        Returns:
            AccountResponse: The safe representation for Web output,
            including the optional avatar_file_id.
        """
        return cls(
            account_id=account.account_id,
            account_username=account.account_username,
            account_email=account.account_email,
            account_role=account.account_role.value if account.account_role else "user",
            account_created_at=account.account_created_at,
            avatar_file_id=account.avatar_file_id,
        )
