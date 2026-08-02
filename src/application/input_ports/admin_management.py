from abc import ABC, abstractmethod

from src.application.domain.account import Account


class AdminManagementPort(ABC):
    """Input port for admin-only account management operations.

    Provides methods to list, search, ban, unban, delete accounts,
    and change user roles. All methods expect the caller to have
    already verified admin authorization at the web boundary.
    """

    @abstractmethod
    def get_account_by_id(self, account_id: int) -> Account | None:
        """Retrieve account by ID. Delegates to repository.

        Args:
            account_id: Unique account identifier.

        Returns:
            Account if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_all_accounts(self, page: int = 1, per_page: int = 20) -> list[Account]:
        """Paginated list of all registered accounts.

        Args:
            page: Page number (1-indexed). Default 1.
            per_page: Items per page. Default 20.

        Returns:
            List of Account domain entities for the given page.
        """
        pass

    @abstractmethod
    def count_all_accounts(self) -> int:
        """Total number of registered accounts.

        Returns:
            Total count.
        """
        pass

    @abstractmethod
    def search_accounts(self, query: str, page: int = 1, per_page: int = 20) -> list[Account]:
        """Search accounts by username or email with pagination.

        Args:
            query: Search string.
            page: Page number (1-indexed). Default 1.
            per_page: Items per page. Default 20.

        Returns:
            List of matching Account entities.
        """
        pass

    @abstractmethod
    def count_search_accounts(self, query: str) -> int:
        """Total accounts matching search query.

        Args:
            query: Search string.

        Returns:
            Total matching count.
        """
        pass

    @abstractmethod
    def delete_account(self, account_id: int) -> None:
        """Delete account. Cleans up avatar file and masks comments.

        Args:
            account_id: ID of account to delete.

        Raises:
            AccountNotFoundError: If account not found.
        """
        pass

    @abstractmethod
    def update_account_role(self, admin_id: int, target_id: int, new_role: str) -> None:
        """Update role of another account.

        Args:
            admin_id: ID of admin performing action.
            target_id: ID of target account.
            new_role: New role string ("user" or "author").

        Raises:
            AuthorizationError: If requester is not admin.
            AccountNotFoundError: If target not found.
            AuthorizationError: If target is another admin.
        """
        pass

    @abstractmethod
    def ban_account(self, admin_id: int, target_account_id: int, ban_reason: str | None) -> None:
        """Ban a user account. Clears session token for immediate disconnect.

        Args:
            admin_id: ID of admin performing action.
            target_account_id: ID of account to ban.
            ban_reason: Optional reason string.

        Raises:
            AuthorizationError: If requester is not admin.
            AccountNotFoundError: If target not found.
            AuthorizationError: If target is another admin.
        """
        pass

    @abstractmethod
    def unban_account(self, admin_id: int, target_account_id: int) -> None:
        """Unban a user account.

        Args:
            admin_id: ID of admin performing action.
            target_account_id: ID of account to unban.

        Raises:
            AuthorizationError: If requester is not admin.
            AccountNotFoundError: If target not found.
        """
        pass
