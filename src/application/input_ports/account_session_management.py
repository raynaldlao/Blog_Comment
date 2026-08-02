from abc import ABC, abstractmethod

from src.application.domain.account import Account


class AccountSessionManagementPort(ABC):
    """Input port for managing user session and profile.

    Provides methods for session lifecycle, identity retrieval,
    and profile attribute updates (avatar, email, password).
    """

    @abstractmethod
    def get_current_account(self) -> Account | None:
        """Retrieve domain Account for the current session.

        Returns:
            Account if authenticated, None otherwise.
        """
        pass

    @abstractmethod
    def terminate_session(self) -> None:
        """Terminate current session (logout)."""
        pass

    @abstractmethod
    def get_account_by_username(self, username: str) -> Account | None:
        """Retrieve Account by username.

        Args:
            username: Username to look up.

        Returns:
            Account if found, None otherwise.
        """
        pass

    @abstractmethod
    def update_profile_photo(self, file_data: bytes, filename: str, mime_type: str) -> str | None:
        """Upload profile photo for current account.

        Args:
            file_data: Raw binary image content.
            filename: Original filename.
            mime_type: Image MIME type.

        Returns:
            UUID of new avatar file, or None if not authenticated.
        """
        pass

    @abstractmethod
    def remove_profile_photo(self) -> bool:
        """Remove profile photo for current account.

        Returns:
            True if avatar removed, False if none existed.
        """
        pass

    @abstractmethod
    def update_email(self, new_email: str) -> None:
        """Update email for current account.

        Raises:
            AuthenticationError: If not signed in.
            EmailAlreadyTakenError: If email already in use.
        """
        pass

    @abstractmethod
    def update_password(self, new_password: str) -> None:
        """Update password for current account.

        Raises:
            AuthenticationError: If not signed in.
        """
        pass

    @abstractmethod
    def delete_own_account(self) -> None:
        """Delete the current user's own account.

        Raises:
            AuthenticationError: If user is not signed in.
        """
        pass
