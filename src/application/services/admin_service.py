import logging

from blog_exceptions import (
    AccountNotFoundError,
    AuthorizationError,
    BlogCommentError,
)
from src.application.domain.account import Account, AccountRole
from src.application.input_ports.admin_management import AdminManagementPort
from src.application.input_ports.comment_management import CommentManagementPort
from src.application.input_ports.file_management import FileManagementPort
from src.application.output_ports.account_repository import AccountRepository

logger = logging.getLogger(__name__)


class AdminService(AdminManagementPort):
    """Admin-only account management operations.

    Handles listing, search, role changes, bans, unbans, and
    cross-domain account deletion (avatar cleanup + comment masking).
    Requires FileManagementPort and CommentManagementPort (mandatory
    -- account deletion is incomplete without both).
    """

    def __init__(
        self,
        account_repository: AccountRepository,
        file_service: FileManagementPort,
        comment_service: CommentManagementPort,
    ):
        """Initialize AdminService with required dependencies.

        Args:
            account_repository: Repository for account data access.
            file_service: Input port for file operations (avatar cleanup).
            comment_service: Input port for comment masking on deletion.
        """
        self.account_repository = account_repository
        self.file_service = file_service
        self.comment_service = comment_service

    def get_account_by_id(self, account_id: int) -> Account | None:
        """Retrieve account by ID.

        Args:
            account_id: Unique account identifier.

        Returns:
            Account if found, None otherwise.
        """
        return self.account_repository.get_by_id(account_id)

    def get_all_accounts(self, page: int = 1, per_page: int = 20) -> list[Account]:
        """Paginated list of all registered accounts.

        Args:
            page: Page number (1-indexed). Default 1.
            per_page: Items per page. Default 20.

        Returns:
            List of Account domain entities for the given page.
        """
        return self.account_repository.get_all_paginated(page, per_page)

    def count_all_accounts(self) -> int:
        """Total number of registered accounts.

        Returns:
            Total count.
        """
        return self.account_repository.count_all()

    def search_accounts(self, query: str, page: int = 1, per_page: int = 20) -> list[Account]:
        """Search accounts by username or email with pagination.

        Args:
            query: Search string.
            page: Page number (1-indexed). Default 1.
            per_page: Items per page. Default 20.

        Returns:
            List of matching Account entities.
        """
        return self.account_repository.search(query, page, per_page)

    def count_search_accounts(self, query: str) -> int:
        """Total accounts matching search query.

        Args:
            query: Search string.

        Returns:
            Total matching count.
        """
        return self.account_repository.count_search(query)

    def delete_account(self, account_id: int) -> None:
        """Delete account. Cleans up avatar file and masks comments.

        Args:
            account_id: ID of account to delete.

        Raises:
            AccountNotFoundError: If no account exists with given ID.
        """
        existing = self.account_repository.get_by_id(account_id)
        if not existing:
            raise AccountNotFoundError(f"Account with ID {account_id} not found.")

        if existing.avatar_file_id:
            try:
                self.file_service.delete_file(existing.avatar_file_id)
            except BlogCommentError:
                logger.warning(
                    "Failed to delete avatar %s for account %s",
                    existing.avatar_file_id, account_id,
                )

        self.comment_service.mask_comments_by_account_id(account_id)
        self.account_repository.delete(account_id)

    def update_account_role(self, admin_id: int, target_id: int, new_role: str) -> None:
        """Update role of target account.

        Args:
            admin_id: Admin performing action.
            target_id: Target account ID.
            new_role: "user" or "author".

        Raises:
            AuthorizationError: If requester not admin.
            AccountNotFoundError: If target not found.
            AuthorizationError: If target is another admin.
        """
        admin = self.account_repository.get_by_id(admin_id)
        if not admin or admin.account_role != AccountRole.ADMIN:
            raise AuthorizationError("Unauthorized.")

        target = self.account_repository.get_by_id(target_id)
        if not target:
            raise AccountNotFoundError("Account not found.")

        if target.account_role == AccountRole.ADMIN:
            raise AuthorizationError("Cannot change another administrator's role.")

        if new_role not in ("user", "author"):
            return

        self.account_repository.update_role(target_id, new_role)

    def ban_account(self, admin_id: int, target_account_id: int, ban_reason: str | None) -> None:
        """Ban account. Clears session token for immediate disconnect.

        Raises:
            AuthorizationError: If requester not admin.
            AccountNotFoundError: If target not found.
            AuthorizationError: If target is another admin.
        """
        admin = self.account_repository.get_by_id(admin_id)
        if not admin or admin.account_role != AccountRole.ADMIN:
            raise AuthorizationError("Unauthorized.")

        target = self.account_repository.get_by_id(target_account_id)
        if not target:
            raise AccountNotFoundError("Account not found.")

        if target.account_role == AccountRole.ADMIN:
            raise AuthorizationError("Cannot ban another administrator.")

        self.account_repository.update_ban_status(target_account_id, True, ban_reason)
        self.account_repository.update_session_token(target_account_id, None)

    def unban_account(self, admin_id: int, target_account_id: int) -> None:
        """Unban account.

        Raises:
            AuthorizationError: If requester not admin.
            AccountNotFoundError: If target not found.
        """
        admin = self.account_repository.get_by_id(admin_id)
        if not admin or admin.account_role != AccountRole.ADMIN:
            raise AuthorizationError("Unauthorized.")

        target = self.account_repository.get_by_id(target_account_id)
        if not target:
            raise AccountNotFoundError("Account not found.")

        self.account_repository.update_ban_status(target_account_id, False, None)
