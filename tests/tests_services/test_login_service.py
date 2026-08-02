from unittest.mock import MagicMock

import pytest

from blog_exceptions import (
    AccountBannedError,
    AuthenticationError,
    BlogCommentError,
    EmailAlreadyTakenError,
)
from src.application.domain.account import Account
from src.application.input_ports.comment_management import CommentManagementPort
from src.application.input_ports.file_management import FileManagementPort
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.output_ports.password_hasher_repository import PasswordHasherRepository
from src.application.services.login_service import LoginService
from tests.test_domain_factories import create_test_account


def _make_login_fixtures(file_service=None, comment_service=None):
    mock_repo = MagicMock(spec=AccountRepository, autospec=True)
    mock_session_repo = MagicMock(spec=AccountSessionRepository, autospec=True)
    mock_hasher = MagicMock(spec=PasswordHasherRepository, autospec=True)
    mock_hasher.verify.return_value = True
    mock_hasher.check_needs_rehash.return_value = False
    service = LoginService(
        account_repository=mock_repo,
        session_repository=mock_session_repo,
        password_hasher_repository=mock_hasher,
        file_service=file_service,
        comment_service=comment_service,
    )
    return mock_repo, mock_session_repo, mock_hasher, service


class TestLoginService:
    def setup_method(self):
        self.mock_repo, self.mock_session_repo, self.mock_hasher, self.service = _make_login_fixtures()

    def test_authenticate_user_success(self):
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account

        result = self.service.authenticate_user(
            username=fake_account.account_username,
            password=fake_account.account_password
        )

        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        self.mock_session_repo.save_account.assert_called_once_with(fake_account)
        assert isinstance(result, Account)
        assert result.account_username == "leia"

    def test_authenticate_user_with_rehash(self):
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account
        self.mock_hasher.verify.return_value = True
        self.mock_hasher.check_needs_rehash.return_value = True
        self.mock_hasher.hash.return_value = "$argon2id$v=19$m=19456,t=2,p=1$new_hash"

        result = self.service.authenticate_user(
            username=fake_account.account_username,
            password="password123"
        )

        self.mock_hasher.check_needs_rehash.assert_called_once()
        self.mock_hasher.hash.assert_called_once_with("password123")
        assert isinstance(result, Account)
        assert result.account_password == "$argon2id$v=19$m=19456,t=2,p=1$new_hash"
        self.mock_repo.save.assert_called_once_with(result)
        self.mock_session_repo.save_account.assert_called_once_with(result)

    def test_authenticate_user_wrong_password(self):
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account
        self.mock_hasher.verify.return_value = False

        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            self.service.authenticate_user(
                username=fake_account.account_username,
                password="bad_password"
            )

        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        self.mock_session_repo.save_account.assert_not_called()

    def test_authenticate_user_non_existent(self):
        self.mock_repo.find_by_username.return_value = None

        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            self.service.authenticate_user(username="phantom", password="nothing")

        self.mock_repo.find_by_username.assert_called_once_with("phantom")
        self.mock_session_repo.save_account.assert_not_called()

    def test_get_current_account(self):
        fake_account = create_test_account()
        self.mock_session_repo.get_account.return_value = fake_account
        result = self.service.get_current_account()
        self.mock_session_repo.get_account.assert_called_once()
        assert result == fake_account

    def test_terminate_session(self):
        self.service.terminate_session()
        self.mock_session_repo.clear.assert_called_once()

    def test_authenticate_user_session_repo_failure(self):
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account
        # Intentionally NOT in blog_exceptions.py: test-only. Exception sufficient.
        # Do not move to blog_exceptions.py.
        self.mock_session_repo.save_account.side_effect = Exception("Storage failure")
        with pytest.raises(Exception, match="Storage failure"):
            self.service.authenticate_user("leia", "password123")

    def test_update_email_success(self):
        fake_account = create_test_account(account_id=1, account_email="old@test.com")
        self.mock_session_repo.get_account.return_value = fake_account
        self.mock_repo.find_by_email.return_value = None
        result = self.service.update_email("new@test.com")
        assert result is None
        self.mock_repo.update_email.assert_called_once_with(1, "new@test.com")

    def test_update_email_taken_returns_error(self):
        fake_account = create_test_account(account_id=1, account_email="old@test.com")
        other = create_test_account(account_id=2, account_email="taken@test.com")
        self.mock_session_repo.get_account.return_value = fake_account
        self.mock_repo.find_by_email.return_value = other

        with pytest.raises(EmailAlreadyTakenError, match="already taken"):
            self.service.update_email("taken@test.com")

        self.mock_repo.update_email.assert_not_called()

    def test_update_email_same_email_returns_none(self):
        fake_account = create_test_account(account_id=1, account_email="same@test.com")
        self.mock_session_repo.get_account.return_value = fake_account

        result = self.service.update_email("same@test.com")

        assert result is None
        self.mock_repo.update_email.assert_not_called()

    def test_update_email_unauthenticated_returns_error(self):
        self.mock_session_repo.get_account.return_value = None

        with pytest.raises(AuthenticationError, match="signed in"):
            self.service.update_email("new@test.com")

        self.mock_repo.update_email.assert_not_called()

    def test_update_password_success(self):
        fake_account = create_test_account(account_id=1)
        self.mock_session_repo.get_account.return_value = fake_account
        self.mock_hasher.hash.return_value = "$argon2id$new_hash"
        result = self.service.update_password("New_Secure1!")
        assert result is None
        self.mock_hasher.hash.assert_called_once_with("New_Secure1!")
        self.mock_repo.update_password.assert_called_once_with(1, "$argon2id$new_hash")

    def test_update_password_unauthenticated_returns_error(self):
        self.mock_session_repo.get_account.return_value = None

        with pytest.raises(AuthenticationError, match="signed in"):
            self.service.update_password("new_secret")

        self.mock_hasher.hash.assert_not_called()
        self.mock_repo.update_password.assert_not_called()

    def test_update_password_empty_returns_none(self):
        fake_account = create_test_account(account_id=1)
        self.mock_session_repo.get_account.return_value = fake_account
        result = self.service.update_password("")
        assert result is None
        self.mock_hasher.hash.assert_not_called()
        self.mock_repo.update_password.assert_not_called()

    def test_authenticate_user_banned(self):
        fake_account = create_test_account(is_banned=True)
        self.mock_repo.find_by_username.return_value = fake_account

        with pytest.raises(AccountBannedError, match="banned"):
            self.service.authenticate_user(
                username=fake_account.account_username,
                password=fake_account.account_password
            )

        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        self.mock_session_repo.save_account.assert_not_called()

    def test_authenticate_user_generates_session_token(self):
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account

        result = self.service.authenticate_user(
            username=fake_account.account_username,
            password="password123"
        )

        assert result.session_token is not None
        assert len(result.session_token) > 30
        self.mock_repo.update_session_token.assert_called_once_with(
            result.account_id, result.session_token
        )
        self.mock_session_repo.save_account.assert_called_once_with(result)

    def test_terminate_session_clears_session_token(self):
        fake_account = create_test_account(account_id=1)
        self.mock_session_repo.get_account.return_value = fake_account
        self.mock_repo.get_by_id.return_value = fake_account

        self.service.terminate_session()

        self.mock_repo.update_session_token.assert_called_once_with(1, None)
        self.mock_session_repo.clear.assert_called_once()


class TestDeleteOwnAccount:
    def setup_method(self):
        self.mock_file_service = MagicMock(spec=FileManagementPort, autospec=True)
        self.mock_comment_service = MagicMock(spec=CommentManagementPort, autospec=True)
        self.mock_repo, self.mock_session_repo, self.mock_hasher, self.service = _make_login_fixtures(
            file_service=self.mock_file_service,
            comment_service=self.mock_comment_service,
        )

    def test_delete_own_account_cascade(self):
        fake_account = create_test_account(account_id=1, account_avatar_file_id="av-123")
        self.mock_session_repo.get_account.return_value = fake_account

        self.service.delete_own_account()

        self.mock_file_service.delete_file.assert_called_once_with("av-123")
        self.mock_comment_service.mask_comments_by_account_id.assert_called_once_with(1)
        self.mock_repo.delete.assert_called_once_with(1)
        self.mock_session_repo.clear.assert_called_once()

    def test_delete_own_account_no_avatar_skips_file_cleanup(self):
        fake_account = create_test_account(account_id=2, account_avatar_file_id=None)
        self.mock_session_repo.get_account.return_value = fake_account

        self.service.delete_own_account()

        self.mock_file_service.delete_file.assert_not_called()
        self.mock_comment_service.mask_comments_by_account_id.assert_called_once_with(2)
        self.mock_repo.delete.assert_called_once_with(2)

    def test_delete_own_account_not_authenticated(self):
        self.mock_session_repo.get_account.return_value = None

        with pytest.raises(AuthenticationError, match="signed in"):
            self.service.delete_own_account()

        self.mock_file_service.delete_file.assert_not_called()
        self.mock_comment_service.mask_comments_by_account_id.assert_not_called()
        self.mock_repo.delete.assert_not_called()

    def test_delete_own_account_avatar_delete_failure_logs_warning(self):
        fake_account = create_test_account(account_id=1, account_avatar_file_id="av-123")
        self.mock_session_repo.get_account.return_value = fake_account
        self.mock_file_service.delete_file.side_effect = BlogCommentError("Storage failed")

        self.service.delete_own_account()

        self.mock_file_service.delete_file.assert_called_once_with("av-123")
        self.mock_comment_service.mask_comments_by_account_id.assert_called_once_with(1)
        self.mock_repo.delete.assert_called_once_with(1)
        self.mock_session_repo.clear.assert_called_once()


class TestProfilePhoto:
    def setup_method(self):
        self.mock_file_service = MagicMock(spec=FileManagementPort, autospec=True)
        self.mock_repo, self.mock_session_repo, self.mock_hasher, self.service = _make_login_fixtures(
            file_service=self.mock_file_service,
        )

    def test_update_profile_photo_no_file_service(self):
        _, _, _, service = _make_login_fixtures(file_service=None)
        result = service.update_profile_photo(b"data", "test.png", "image/png")
        assert result is None

    def test_update_profile_photo_unauthenticated(self):
        self.mock_session_repo.get_account.return_value = None
        result = self.service.update_profile_photo(b"data", "test.png", "image/png")
        assert result is None

    def test_update_profile_photo_delete_failure_logs_warning(self):
        fake_account = create_test_account(account_id=1, account_avatar_file_id="old-av")
        self.mock_session_repo.get_account.return_value = fake_account
        self.mock_file_service.upload_file.return_value = MagicMock(file_id="new-av")
        self.mock_file_service.delete_file.side_effect = BlogCommentError("Storage failed")
        result = self.service.update_profile_photo(b"data", "test.png", "image/png")
        assert result == "new-av"
        self.mock_file_service.delete_file.assert_called_once_with("old-av")

    def test_remove_profile_photo_no_file_service(self):
        _, _, _, service = _make_login_fixtures(file_service=None)
        result = service.remove_profile_photo()
        assert result is False

    def test_remove_profile_photo_unauthenticated(self):
        self.mock_session_repo.get_account.return_value = None
        result = self.service.remove_profile_photo()
        assert result is False

    def test_remove_profile_photo_no_avatar(self):
        fake_account = create_test_account(account_id=1, account_avatar_file_id=None)
        self.mock_session_repo.get_account.return_value = fake_account
        result = self.service.remove_profile_photo()
        assert result is False
        self.mock_file_service.delete_file.assert_not_called()

    def test_remove_profile_photo_delete_failure(self):
        fake_account = create_test_account(account_id=1, account_avatar_file_id="av-123")
        self.mock_session_repo.get_account.return_value = fake_account
        self.mock_file_service.delete_file.side_effect = BlogCommentError("Storage failed")
        result = self.service.remove_profile_photo()
        assert result is False

    def test_remove_profile_photo_success(self):
        fake_account = create_test_account(account_id=1, account_avatar_file_id="av-123")
        self.mock_session_repo.get_account.return_value = fake_account
        result = self.service.remove_profile_photo()
        assert result is True
        self.mock_file_service.delete_file.assert_called_once_with("av-123")
        updated = self.mock_repo.update_avatar.call_args
        assert updated is not None
        assert updated[0][1] is None

    def test_update_avatar_unauthenticated_returns_none(self):
        self.mock_session_repo.get_account.return_value = None
        result = self.service._update_avatar("new-av")
        assert result is None
        self.mock_repo.update_avatar.assert_not_called()
