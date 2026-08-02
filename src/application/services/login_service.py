import logging
import secrets

from blog_exceptions import (
    AccountBannedError,
    AuthenticationError,
    BlogCommentError,
    EmailAlreadyTakenError,
)
from src.application.domain.account import Account
from src.application.input_ports.account_session_management import AccountSessionManagementPort
from src.application.input_ports.comment_management import CommentManagementPort
from src.application.input_ports.file_management import FileManagementPort
from src.application.input_ports.login_management import LoginManagementPort
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.output_ports.password_hasher_repository import PasswordHasherRepository

logger = logging.getLogger(__name__)


class LoginService(LoginManagementPort, AccountSessionManagementPort):
    """Service for authentication, session lifecycle, and profile management.

    Implements LoginManagementPort (authentication) and
    AccountSessionManagementPort (session, profile).
    """

    def __init__(
        self,
        account_repository: AccountRepository,
        session_repository: AccountSessionRepository,
        password_hasher_repository: PasswordHasherRepository,
        file_service: FileManagementPort | None = None,
        comment_service: CommentManagementPort | None = None,
    ):
        """Initialize with account, session, hasher, and optional file and comment services.

        Args:
            account_repository: Repository for account data access.
            session_repository: Output port for session persistence.
            password_hasher_repository: Port for password verification.
            file_service: Optional input port for avatar upload/delete.
            comment_service: Optional input port for comment masking on account delete.
        """
        self.account_repository = account_repository
        self.session_repository = session_repository
        self.password_hasher_repository = password_hasher_repository
        self.file_service = file_service
        self.comment_service = comment_service

    def authenticate_user(self, username: str, password: str) -> Account:
        """
        Authenticates a user by verifying credentials.

        If successful, a new session token is generated and persisted
        in the database (invalidating any previous session), and the
        account is saved in the session cookie.
        If the existing password hash uses outdated parameters,
        it is seamlessly upgraded to the current Argon2 settings.

        Args:
            username (str): The username provided by the user.
            password (str): The plaintext password provided by the user.

        Returns:
            Account: The authenticated Account instance.

        Raises:
            AuthenticationError: If the username or password is invalid.
            AccountBannedError: If the account is banned.
        """

        account = self.account_repository.find_by_username(username)
        if not account:
            raise AuthenticationError("Invalid username or password.")

        if self.password_hasher_repository.verify(password, account.account_password):
            if account.is_banned:
                raise AccountBannedError("This account has been banned.")

            if self.password_hasher_repository.check_needs_rehash(account.account_password):
                new_hash = self.password_hasher_repository.hash(password)
                account.account_password = new_hash
                self.account_repository.save(account)

            token = secrets.token_urlsafe(32)
            account.session_token = token
            self.account_repository.update_session_token(account.account_id, token)
            self.session_repository.save_account(account)
            return account

        raise AuthenticationError("Invalid username or password.")

    def get_current_account(self) -> Account | None:
        """
        Retrieves the domain Account associated with the current session.

        Returns:
            Account | None: The domain representation of the connected user,
                            or None if unauthenticated.
        """
        return self.session_repository.get_account()

    def terminate_session(self) -> None:
        """
        Terminates the current active session, effectively logging the user out.

        Clears the session token in the database before wiping the session
        cookie, ensuring the token cannot be reused.
        """
        current = self.get_current_account()
        if current:
            self.account_repository.update_session_token(current.account_id, None)
        self.session_repository.clear()

    def get_account_by_username(self, username: str) -> Account | None:
        """
        Retrieves a domain Account by its unique username via the repository.

        Args:
            username: The username to look up.

        Returns:
            Account | None: The domain Account if found, None otherwise.
        """
        return self.account_repository.find_by_username(username)

    def _update_avatar(self, avatar_file_id: str | None) -> None:
        account = self.get_current_account()
        if account is None:
            return
        self.account_repository.update_avatar(account.account_id, avatar_file_id)

    def update_email(self, new_email: str) -> None:
        """
        Updates the email address for the currently logged-in account.

        Retrieves the current account from the session, checks that the new
        email is not already used by a different account, and persists the
        change via the account repository.

        Args:
            new_email: The new email address to set.

        Raises:
            AuthenticationError: If the user is not signed in.
            EmailAlreadyTakenError: If the email is already in use by another account.
        """
        account = self.get_current_account()
        if not account:
            raise AuthenticationError("You must be signed in to update your email.")

        if new_email == account.account_email:
            return

        existing = self.account_repository.find_by_email(new_email)
        if existing and existing.account_id != account.account_id:
            raise EmailAlreadyTakenError("This username or email is already taken.")

        self.account_repository.update_email(account.account_id, new_email)

    def update_password(self, new_password: str) -> None:
        """
        Updates the password for the currently logged-in account.

        Hashes the new password and persists it via the account repository.
        The caller (DTO layer) is responsible for password strength validation.

        Args:
            new_password: The new plaintext password to set.

        Raises:
            AuthenticationError: If the user is not signed in.
        """
        account = self.get_current_account()
        if not account:
            raise AuthenticationError("You must be signed in to update your password.")

        if not new_password:
            return

        new_hash = self.password_hasher_repository.hash(new_password)
        self.account_repository.update_password(account.account_id, new_hash)

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
            str | None: The UUID of the new avatar file, or None if not authenticated
                        or if file_service is not configured.
        """
        if not self.file_service:
            return None
        account = self.get_current_account()
        if not account:
            return None

        file_record = self.file_service.upload_file(filename=filename, data=file_data, mime_type=mime_type)

        old_avatar_id = account.avatar_file_id
        if old_avatar_id:
            try:
                self.file_service.delete_file(old_avatar_id)
            except BlogCommentError:
                logger.warning(
                    "Failed to delete old avatar %s for account %s",
                    old_avatar_id, account.account_id,
                )

        self._update_avatar(file_record.file_id)
        return file_record.file_id

    def remove_profile_photo(self) -> bool:
        """
        Removes the profile photo for the currently authenticated account.

        Deletes the stored file and clears the avatar reference.
        Idempotent — returns False if the user has no avatar or is not authenticated.

        Returns:
            bool: True if the avatar was removed, False if no avatar existed
                  or not authenticated.

        Raises:
            BlogCommentError: If file storage operation fails (logged, not re-raised).
        """
        if not self.file_service:
            return False
        account = self.get_current_account()
        if not account or not account.avatar_file_id:
            return False

        try:
            self.file_service.delete_file(account.avatar_file_id)
        except BlogCommentError:
            return False

        self._update_avatar(None)
        return True

    def delete_own_account(self) -> None:
        """Delete the currently authenticated account.

        Cleans up avatar file if present, masks the user's comments,
        then deletes the account record and clears the session.

        Raises:
            AuthenticationError: If the user is not signed in.
        """
        account = self.get_current_account()
        if not account:
            raise AuthenticationError("You must be signed in.")
        if self.file_service and account.avatar_file_id:
            try:
                self.file_service.delete_file(account.avatar_file_id)
            except BlogCommentError:
                logger.warning(
                    "Failed to delete avatar %s for account %s",
                    account.avatar_file_id, account.account_id,
                )
        if self.comment_service:
            self.comment_service.mask_comments_by_account_id(account.account_id)
        self.account_repository.delete(account.account_id)
        self.session_repository.clear()
