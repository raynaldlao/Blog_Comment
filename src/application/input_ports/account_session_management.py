from abc import ABC, abstractmethod

from src.application.domain.account import Account


class AccountSessionManagementPort(ABC):
    """
    Input Port for managing the user's active session and account profile.
    Provides methods for the interface layer to retrieve identity, manage
    the session lifecycle, and update profile attributes including avatar.
    """

    @abstractmethod
    def get_current_account(self) -> Account | None:
        """
        Retrieves the domain Account associated with the current session.

        Returns:
            Account | None: The domain representation of the connected user,
                            or None if unauthenticated.
        """
        pass

    @abstractmethod
    def terminate_session(self) -> None:
        """
        Terminates the current active session, effectively logging the user out.
        """
        pass

    @abstractmethod
    def get_account_by_username(self, username: str) -> Account | None:
        """
        Retrieves a domain Account by its unique username.

        Args:
            username: The username to look up.

        Returns:
            Account | None: The domain Account if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_account_by_id(self, account_id: int) -> Account | None:
        """
        Retrieves a domain Account by its unique identifier.

        Args:
            account_id: The unique identifier of the account.

        Returns:
            Account | None: The domain Account if found, None otherwise.
        """
        pass

    @abstractmethod
    def update_profile_photo(self, file_data: bytes, filename: str, mime_type: str) -> str | None:
        """
        Uploads a new profile photo for the currently authenticated account.

        Delegates file storage to the file service, cleans up any existing
        avatar, and persists the new file reference on the account.

        Args:
            file_data: Raw binary content of the image file.
            filename: Original filename with extension.
            mime_type: MIME type of the uploaded image.

        Returns:
            str | None: The UUID of the new avatar file, or None if not authenticated.
        """
        pass

    @abstractmethod
    def remove_profile_photo(self) -> bool:
        """
        Removes the profile photo for the currently authenticated account.

        Deletes the stored file and clears the avatar reference.
        Idempotent — returns False if the user has no avatar.

        Returns:
            bool: True if the avatar was removed, False if no avatar existed.
        """
        pass

    @abstractmethod
    def update_avatar(self, avatar_file_id: str | None) -> None:
        """
        Sets or clears the avatar_file_id for the currently authenticated account.

        Pass None to remove the avatar reference.

        Args:
            avatar_file_id: The UUID of the uploaded avatar file, or None to clear.
        """
        pass

    @abstractmethod
    def update_email(self, new_email: str) -> None:
        """
        Updates the email address for the currently authenticated account.

        Args:
            new_email: The new email address to set.

        Raises:
            AuthenticationError: If the user is not signed in.
            EmailAlreadyTakenError: If the email is already in use by another account.
        """
        pass

    @abstractmethod
    def update_password(self, new_password: str) -> None:
        """
        Updates the password for the currently authenticated account.
        Hashes the new password and persists it via the account repository.

        Args:
            new_password: The new plaintext password to set.

        Raises:
            AuthenticationError: If the user is not signed in.
        """
        pass

    @abstractmethod
    def get_all_accounts(self, page: int = 1, per_page: int = 20) -> list[Account]:
        """
        Retrieves a paginated list of all registered accounts.

        Intended for admin use only. The calling adapter is responsible
        for enforcing role-based access control.

        Args:
            page: The page number (1-indexed). Defaults to 1.
            per_page: The number of items per page. Defaults to 20.

        Returns:
            list[Account]: A list of Account domain entities for the given page.
        """
        pass

    @abstractmethod
    def count_all_accounts(self) -> int:
        """
        Returns the total number of registered accounts.

        Intended for admin use only, paired with get_all_accounts()
        to compute pagination metadata.

        Returns:
            int: The total count of accounts.
        """
        pass

    @abstractmethod
    def search_accounts(self, query: str, page: int = 1, per_page: int = 20) -> list[Account]:
        """
        Searches accounts by username or email with pagination.

        Intended for admin use only. The calling adapter is responsible
        for enforcing role-based access control.

        Args:
            query: The search string to match against username or email.
            page: The page number (1-indexed). Defaults to 1.
            per_page: The number of items per page. Defaults to 20.

        Returns:
            list[Account]: A list of matching Account domain entities
                for the given page.
        """
        pass

    @abstractmethod
    def count_search_accounts(self, query: str) -> int:
        """
        Returns the total number of accounts matching the search query.

        Intended for admin use only, paired with search_accounts()
        to compute pagination metadata.

        Args:
            query: The search string to match against username or email.

        Returns:
            int: The total count of matching accounts.
        """
        pass

    @abstractmethod
    def ban_account(self, admin_id: int, target_account_id: int, ban_reason: str | None) -> None:
        """
        Bans a user account. Only admins can ban non-admin accounts.

        Args:
            admin_id: The unique identifier of the admin performing the action.
            target_account_id: The unique identifier of the account to ban.
            ban_reason: Optional reason for the ban.

        Raises:
            AuthorizationError: If the requester is not an admin.
            AccountNotFoundError: If the target account is not found.
            AuthorizationError: If the target is another admin.
        """
        pass

    @abstractmethod
    def unban_account(self, admin_id: int, target_account_id: int) -> None:
        """
        Unbans a user account. Only admins can unban accounts.

        Args:
            admin_id: The unique identifier of the admin performing the action.
            target_account_id: The unique identifier of the account to unban.

        Raises:
            AuthorizationError: If the requester is not an admin.
            AccountNotFoundError: If the target account is not found.
        """
        pass

    @abstractmethod
    def delete_account(self, account_id: int) -> None:
        """
        Deletes a user account by its unique identifier.

        Cleans up the associated avatar file and masks the account's
        comments before deleting the account record. The database handles
        orphaned articles via ON DELETE SET NULL.

        Args:
            account_id: The unique identifier of the account to delete.

        Raises:
            AccountNotFoundError: If no account exists with the given id.
        """
        pass

    @abstractmethod
    def update_account_role(self, admin_id: int, target_id: int, new_role: str) -> None:
        """
        Allows an admin user to update the role of another user account.

        Args:
            admin_id: The unique identifier of the admin performing the action.
            target_id: The unique identifier of the account whose role is to be updated.
            new_role: The new role string ("user" or "author").

        Raises:
            AuthorizationError: If the requester is not an admin.
            AccountNotFoundError: If the target account is not found.
            AuthorizationError: If the target is another admin.
        """
        pass
