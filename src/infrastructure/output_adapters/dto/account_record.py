from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.application.domain.account import Account, AccountRole


class AccountRecord(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for account database records.

    This class faithfully mirrors the 'accounts' table schema and provides
    validation when loading data from the persistence layer.
    """

    model_config = ConfigDict(from_attributes=True)

    account_id: int
    account_username: str
    account_password: str
    account_email: str
    account_role: str
    account_created_at: datetime | None

    def to_domain(self) -> Account:
        """
        Converts the database record into a domain Account entity.

        Returns:
            Account: The corresponding domain entity, including the
            conversion of the 'account_role' string to an AccountRole enum.
        """
        return Account(
            account_id=self.account_id,
            account_username=self.account_username,
            account_password=self.account_password,
            account_email=self.account_email,
            account_role=AccountRole(self.account_role),
            account_created_at=self.account_created_at,
        )
