from unittest.mock import MagicMock

from src.application.domain.account import Account, AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.account_session_repository import AccountSessionRepository
from src.application.output_ports.password_hasher_repository import PasswordHasherRepository
from src.application.services.login_service import LoginService
from tests.exceptions_tests import ExceptionTest
from tests.test_domain_factories import create_test_account


class TestLoginService:
    def setup_method(self):
        self.mock_repo = MagicMock(spec=AccountRepository, autospec=True)
        self.mock_session_repo = MagicMock(spec=AccountSessionRepository, autospec=True)
        self.mock_hasher = MagicMock(spec=PasswordHasherRepository, autospec=True)
        self.mock_hasher.verify.return_value = True
        self.mock_hasher.check_needs_rehash.return_value = False

        self.service = LoginService(
            account_repository=self.mock_repo,
            session_repository=self.mock_session_repo,
            password_hasher_repository=self.mock_hasher
        )

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

        result = self.service.authenticate_user(
            username=fake_account.account_username,
            password="bad_password"
        )

        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        self.mock_session_repo.save_account.assert_not_called()
        assert result == "Invalid username or password."

    def test_authenticate_user_non_existent(self):
        self.mock_repo.find_by_username.return_value = None
        result = self.service.authenticate_user(username="phantom", password="nothing")
        self.mock_repo.find_by_username.assert_called_once_with("phantom")
        self.mock_session_repo.save_account.assert_not_called()
        assert result == "Invalid username or password."

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
        import pytest
        fake_account = create_test_account()
        self.mock_repo.find_by_username.return_value = fake_account
        self.mock_session_repo.save_account.side_effect = ExceptionTest("Storage failure")
        with pytest.raises(ExceptionTest, match="Storage failure"):
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
        result = self.service.update_email("taken@test.com")
        assert result == "This email is already taken."
        self.mock_repo.update_email.assert_not_called()

    def test_update_email_unauthenticated_returns_error(self):
        self.mock_session_repo.get_account.return_value = None
        result = self.service.update_email("new@test.com")
        assert result == "You must be signed in to update your email."
        self.mock_repo.update_email.assert_not_called()

    def test_update_password_success(self):
        fake_account = create_test_account(account_id=1)
        self.mock_session_repo.get_account.return_value = fake_account
        self.mock_hasher.hash.return_value = "$argon2id$new_hash"
        result = self.service.update_password("new_secret")
        assert result is None
        self.mock_hasher.hash.assert_called_once_with("new_secret")
        self.mock_repo.update_password.assert_called_once_with(1, "$argon2id$new_hash")

    def test_update_password_unauthenticated_returns_error(self):
        self.mock_session_repo.get_account.return_value = None
        result = self.service.update_password("new_secret")
        assert result == "You must be signed in to update your password."
        self.mock_hasher.hash.assert_not_called()
        self.mock_repo.update_password.assert_not_called()

    def test_update_password_empty_returns_error(self):
        fake_account = create_test_account(account_id=1)
        self.mock_session_repo.get_account.return_value = fake_account
        result = self.service.update_password("")
        assert result == "Password is required."
        self.mock_hasher.hash.assert_not_called()
        self.mock_repo.update_password.assert_not_called()

    def test_delete_account_success(self):
        fake_account = create_test_account(account_id=1)
        self.mock_repo.get_by_id.return_value = fake_account
        self.service.delete_account(fake_account.account_id)
        self.mock_repo.delete.assert_called_once_with(fake_account.account_id)

    def test_delete_account_not_found_raises_value_error(self):
        self.mock_repo.get_by_id.return_value = None
        import pytest
        with pytest.raises(ValueError, match="not found"):
            self.service.delete_account(999)
        self.mock_repo.delete.assert_not_called()

    def test_update_role_success(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target}.get(cid)

        result = self.service.update_account_role(
            admin_id=1, target_id=2, new_role="author"
        )

        assert result is None
        self.mock_repo.update_role.assert_called_once_with(2, "author")

    def test_update_role_account_not_found(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin}.get(cid)

        result = self.service.update_account_role(
            admin_id=1, target_id=999, new_role="author"
        )

        assert result == "Account not found."
        self.mock_repo.update_role.assert_not_called()

    def test_update_role_not_admin(self):
        user = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.return_value = user

        result = self.service.update_account_role(
            admin_id=1, target_id=2, new_role="author"
        )

        assert result == "Unauthorized."
        self.mock_repo.update_role.assert_not_called()

    def test_update_role_target_is_admin(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target_admin = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target_admin}.get(cid)

        result = self.service.update_account_role(
            admin_id=1, target_id=2, new_role="user"
        )

        assert result == "Cannot change role of another admin."
        self.mock_repo.update_role.assert_not_called()

    def test_update_role_invalid_role(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target}.get(cid)

        result = self.service.update_account_role(
            admin_id=1, target_id=2, new_role="superadmin"
        )

        assert result == "Invalid role."
        self.mock_repo.update_role.assert_not_called()

    def test_ban_account_success(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target}.get(cid)

        result = self.service.ban_account(admin_id=1, target_account_id=2, ban_reason="Spam")

        assert result is None
        self.mock_repo.update_ban_status.assert_called_once_with(2, True, "Spam")

    def test_ban_account_not_found(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin}.get(cid)

        result = self.service.ban_account(admin_id=1, target_account_id=999, ban_reason="Spam")

        assert result == "Account not found."
        self.mock_repo.update_ban_status.assert_not_called()

    def test_ban_account_target_is_admin(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target_admin = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target_admin}.get(cid)

        result = self.service.ban_account(admin_id=1, target_account_id=2, ban_reason="Spam")

        assert result == "Cannot ban another admin."
        self.mock_repo.update_ban_status.assert_not_called()

    def test_unban_account_success(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target}.get(cid)

        result = self.service.unban_account(admin_id=1, target_account_id=2)

        assert result is None
        self.mock_repo.update_ban_status.assert_called_once_with(2, False, None)

    def test_authenticate_user_banned(self):
        fake_account = create_test_account(is_banned=True)
        self.mock_repo.find_by_username.return_value = fake_account

        result = self.service.authenticate_user(
            username=fake_account.account_username,
            password=fake_account.account_password
        )

        self.mock_repo.find_by_username.assert_called_once_with(fake_account.account_username)
        self.mock_session_repo.save_account.assert_not_called()
        assert result == "This account has been banned."
