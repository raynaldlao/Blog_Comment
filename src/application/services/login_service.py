import logging
import re
import secrets

from blog_exceptions import (
    AccountBannedError,
    AccountNotFoundError,
    AuthenticationError,
    AuthorizationError,
    BlogCommentError,
    EmailAlreadyTakenError,
    WeakPasswordError,
)
from src.application.domain.account import Account, AccountRole
from src.application.input_ports.account_session_management import AccountSessionManagementPort
from src.application.input_ports.comment_management import CommentManagementPort
from src.application.input_ports.file_management import FileManagementPort
from src.application.input_ports.login_management import LoginManagementPort
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.output_ports.password_hasher_repository import PasswordHasherRepository


class LoginService(LoginManagementPort, AccountSessionManagementPort):
    """
    Service responsible for handling user authentication and session lifecycle.
    Implements both LoginManagementPort (for authentication) and
    AccountSessionManagementPort (for session, profile, and account management).
    Orchestrates cross-cutting operations like account deletion and avatar
    management that span multiple domains (file, comment, account).
    """

    def __init__(
        self,
        account_repository: AccountRepository,
        session_repository: AccountSessionRepository,
        password_hasher_repository: PasswordHasherRepository,
        file_service: FileManagementPort | None = None,
        comment_service: CommentManagementPort | None = None,
    ):
        """
        Initializes the service with account repository, session management,
        password hashing, and optional cross-domain services.

        file_service and comment_service are optional for backward compatibility
        (tests that mock LoginService directly). In production they are always
        provided via blog_comment_application.py.

        Args:
            account_repository (AccountRepository): The repository for account data access.
            session_repository (AccountSessionRepository): The output port for session persistence.
            password_hasher_repository (PasswordHasherRepository): The port for password verification operations.
            file_service (FileManagementPort | None): Input port for file operations (avatar upload/delete).
            comment_service (CommentManagementPort | None): Input port for comment masking on account deletion.
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
            raise AuthenticationError("Nom d'utilisateur ou mot de passe invalide.")

        if self.password_hasher_repository.verify(password, account.account_password):
            if account.is_banned:
                raise AccountBannedError("Ce compte a été banni.")

            if self.password_hasher_repository.check_needs_rehash(account.account_password):
                new_hash = self.password_hasher_repository.hash(password)
                account.account_password = new_hash
                self.account_repository.save(account)

            token = secrets.token_urlsafe(32)
            account.session_token = token
            self.account_repository.update_session_token(account.account_id, token)
            self.session_repository.save_account(account)
            return account

        raise AuthenticationError("Nom d'utilisateur ou mot de passe invalide.")

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

    def get_account_by_id(self, account_id: int) -> Account | None:
        """
        Retrieves a domain Account by its unique identifier via the repository.

        Args:
            account_id: The unique identifier of the account.

        Returns:
            Account | None: The domain Account if found, None otherwise.
        """
        return self.account_repository.get_by_id(account_id)

    def update_avatar(self, avatar_file_id: str | None) -> None:
        """
        Sets or clears the avatar_file_id for the currently authenticated account.

        Retrieves the current account from the session and delegates
        the persistence update to the account repository.

        Pass None to remove the avatar reference.

        Args:
            avatar_file_id: The UUID of the uploaded avatar file, or None to clear.
        """
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
            raise AuthenticationError("Vous devez être connecté pour modifier votre email.")

        if new_email == account.account_email:
            return

        existing = self.account_repository.find_by_email(new_email)
        if existing and existing.account_id != account.account_id:
            raise EmailAlreadyTakenError("Ce nom d'utilisateur ou cet email est déjà pris.")

        self.account_repository.update_email(account.account_id, new_email)

    def update_password(self, new_password: str) -> None:
        """
        Updates the password for the currently logged-in account.

        Validates password strength (lowercase, uppercase, special char),
        then hashes and persists via the account repository.

        Args:
            new_password: The new plaintext password to set.

        Raises:
            AuthenticationError: If the user is not signed in.
            WeakPasswordError: If password lacks lowercase, uppercase,
                or special character.
        """
        account = self.get_current_account()
        if not account:
            raise AuthenticationError("Vous devez être connecté pour modifier votre mot de passe.")

        if not new_password:
            return

        if not re.search(r"[a-z]", new_password):
            raise WeakPasswordError("Le mot de passe doit contenir au moins une minuscule.")
        if not re.search(r"[A-Z]", new_password):
            raise WeakPasswordError("Le mot de passe doit contenir au moins une majuscule.")
        if not re.search(r"[^a-zA-Z0-9]", new_password):
            raise WeakPasswordError("Le mot de passe doit contenir au moins un caractère spécial.")

        new_hash = self.password_hasher_repository.hash(new_password)
        self.account_repository.update_password(account.account_id, new_hash)

    def get_all_accounts(self, page: int = 1, per_page: int = 20) -> list[Account]:
        """
        Retrieves a paginated list of all registered accounts.

        Args:
            page: The page number (1-indexed). Defaults to 1.
            per_page: The number of items per page. Defaults to 20.

        Returns:
            list[Account]: A list of Account domain entities for the given page.
        """
        return self.account_repository.get_all_paginated(page, per_page)

    def count_all_accounts(self) -> int:
        """
        Returns the total number of registered accounts.

        Returns:
            int: The total count of accounts.
        """
        return self.account_repository.count_all()

    def search_accounts(self, query: str, page: int = 1, per_page: int = 20) -> list[Account]:
        """
        Searches accounts by username or email with pagination.

        Args:
            query: The search string to match against username or email.
            page: The page number (1-indexed). Defaults to 1.
            per_page: The number of items per page. Defaults to 20.

        Returns:
            list[Account]: A list of matching Account domain entities
                for the given page.
        """
        return self.account_repository.search(query, page, per_page)

    def count_search_accounts(self, query: str) -> int:
        """
        Returns the total number of accounts matching the search query.

        Args:
            query: The search string to match against username or email.

        Returns:
            int: The total count of matching accounts.
        """
        return self.account_repository.count_search(query)

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
                logging.getLogger(__name__).warning(
                    "Failed to delete old avatar %s for account %s",
                    old_avatar_id, account.account_id,
                )

        self.update_avatar(file_record.file_id)
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

        self.update_avatar(None)
        return True

    def delete_account(self, account_id: int) -> None:
        """
        Deletes a user account by its unique identifier.

        Cleans up the associated avatar file and masks the account's
        comments before deleting the account record. The database handles
        orphaned articles via ON DELETE SET NULL.

        Args:
            account_id: The unique identifier of the account to delete.

        Raises:
            AccountNotFoundError: If no account with the given ID exists.
        """
        existing = self.account_repository.get_by_id(account_id)
        if not existing:
            raise AccountNotFoundError(f"Compte avec l'identifiant {account_id} introuvable.")

        if existing.avatar_file_id and self.file_service:
            try:
                self.file_service.delete_file(existing.avatar_file_id)
            except BlogCommentError:
                logging.getLogger(__name__).warning(
                    "Failed to delete avatar %s for account %s",
                    existing.avatar_file_id, account_id,
                )

        if self.comment_service:
            self.comment_service.mask_comments_by_account_id(account_id)

        self.account_repository.delete(account_id)

    def update_account_role(self, admin_id: int, target_id: int, new_role: str) -> None:
        """
        Allows an admin user to update the role of another user account.

        Validates that the requester is an admin, the target exists,
        the target is not an admin, and the new role is valid.

        Args:
            admin_id: The unique identifier of the admin performing the action.
            target_id: The unique identifier of the account whose role is to be updated.
            new_role: The new role string ("user" or "author").

        Raises:
            AuthorizationError: If the requester is not an admin.
            AccountNotFoundError: If the target account is not found.
            AuthorizationError: If the target is another admin.
        """
        admin = self.account_repository.get_by_id(admin_id)
        if not admin or admin.account_role != AccountRole.ADMIN:
            raise AuthorizationError("Non autorisé.")

        target = self.account_repository.get_by_id(target_id)
        if not target:
            raise AccountNotFoundError("Compte introuvable.")

        if target.account_role == AccountRole.ADMIN:
            raise AuthorizationError("Impossible de modifier le rôle d'un autre administrateur.")

        if new_role not in ("user", "author"):
            return

        self.account_repository.update_role(target_id, new_role)

    def ban_account(self, admin_id: int, target_account_id: int, ban_reason: str | None) -> None:
        """
        Bans a user account. Only admins can ban non-admin accounts.

        Clears the session token to force immediate disconnection
        on the next request from any active session.

        Args:
            admin_id: The unique identifier of the admin performing the action.
            target_account_id: The unique identifier of the account to ban.
            ban_reason: Optional reason for the ban.

        Raises:
            AuthorizationError: If the requester is not an admin.
            AccountNotFoundError: If the target account is not found.
            AuthorizationError: If the target is another admin.
        """
        admin = self.account_repository.get_by_id(admin_id)
        if not admin or admin.account_role != AccountRole.ADMIN:
            raise AuthorizationError("Non autorisé.")

        target = self.account_repository.get_by_id(target_account_id)
        if not target:
            raise AccountNotFoundError("Compte introuvable.")

        if target.account_role == AccountRole.ADMIN:
            raise AuthorizationError("Impossible de bannir un autre administrateur.")

        self.account_repository.update_ban_status(target_account_id, True, ban_reason)
        self.account_repository.update_session_token(target_account_id, None)

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
        admin = self.account_repository.get_by_id(admin_id)
        if not admin or admin.account_role != AccountRole.ADMIN:
            raise AuthorizationError("Non autorisé.")

        target = self.account_repository.get_by_id(target_account_id)
        if not target:
            raise AccountNotFoundError("Compte introuvable.")

        self.account_repository.update_ban_status(target_account_id, False, None)
