from abc import ABC, abstractmethod

from src.application.domain.account import Account


class AccountSessionManagementPort(ABC):
    """
    Input Port for managing the user's active session.
    Provides methods for the interface layer to retrieve identity and terminate sessions.
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
    def update_avatar(self, avatar_file_id: str | None) -> None:
        """
        Sets or clears the avatar_file_id for the currently authenticated account.

        Pass None to remove the avatar reference.

        Args:
            avatar_file_id: The UUID of the uploaded avatar file, or None to clear.
        """
        pass

    @abstractmethod
    def update_email(self, new_email: str) -> str | None:
        """
        Updates the email address for the currently authenticated account.

        Validates that the new email is not already in use by another account
        before persisting the change.

        Args:
            new_email: The new email address to set.

        Returns:
            str | None: None on success, or an error message string if
                the email is already taken or the user is not authenticated.
        """
        pass

    @abstractmethod
    def update_password(self, new_password: str) -> str | None:
        """
        Updates the password for the currently authenticated account.

        Hashes the new password and persists it via the account repository.

        Args:
            new_password: The new plaintext password to set.

        Returns:
            str | None: None on success, or an error message string if
                the user is not authenticated.
        """
        pass

    @abstractmethod
    def get_all_accounts(self) -> list[Account]:
        """
        Retrieves all registered accounts.

        Intended for admin use only. The calling adapter is responsible
        for enforcing role-based access control.

        Returns:
            list[Account]: A list of all Account domain entities.
        """
        pass

    @abstractmethod
    def delete_account(self, account_id: int) -> None:
        """
        Deletes a user account by its unique identifier.

        The associated avatar file should be cleaned up by the caller
        before invoking this method. The database handles orphaned
        articles via ON DELETE SET NULL and comments via ON DELETE CASCADE.

        Args:
            account_id: The unique identifier of the account to delete.
        """
        pass

    @abstractmethod
    def update_account_role(self, admin_id: int, target_id: int, new_role: str) -> str | None:
        """
        Allows an admin user to update the role of another user account.

        Args:
            admin_id: The unique identifier of the admin performing the action.
            target_id: The unique identifier of the account whose role is to be updated.
            new_role: The new role string ("user" or "author").

        Returns:
            str | None: None on success, or an error message string if the operation fails.
        """
        pass
