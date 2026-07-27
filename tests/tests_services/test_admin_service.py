from unittest.mock import MagicMock

import pytest

from blog_exceptions import (
    AccountNotFoundError,
    AuthorizationError,
    BlogCommentError,
)
from src.application.domain.account import AccountRole
from src.application.input_ports.comment_management import CommentManagementPort
from src.application.input_ports.file_management import FileManagementPort
from src.application.output_ports.account_repository import AccountRepository
from src.application.services.admin_service import AdminService
from tests.test_domain_factories import create_test_account


class TestAdminService:
    def setup_method(self):
        self.mock_repo = MagicMock(spec=AccountRepository, autospec=True)
        self.mock_file_service = MagicMock(spec=FileManagementPort, autospec=True)
        self.mock_comment_service = MagicMock(spec=CommentManagementPort, autospec=True)

        self.service = AdminService(
            account_repository=self.mock_repo,
            file_service=self.mock_file_service,
            comment_service=self.mock_comment_service,
        )

    def test_delete_account_success(self):
        fake_account = create_test_account(account_id=1)
        self.mock_repo.get_by_id.return_value = fake_account
        self.service.delete_account(fake_account.account_id)
        self.mock_repo.delete.assert_called_once_with(fake_account.account_id)

    def test_delete_account_not_found_raises_account_not_found_error(self):
        self.mock_repo.get_by_id.return_value = None
        with pytest.raises(AccountNotFoundError, match="not found"):
            self.service.delete_account(999)
        self.mock_repo.delete.assert_not_called()

    def test_delete_account_cleans_up_avatar_and_masks_comments(self):
        fake_account = create_test_account(account_id=1, account_avatar_file_id="avatar-id")
        self.mock_repo.get_by_id.return_value = fake_account

        self.service.delete_account(1)

        self.mock_file_service.delete_file.assert_called_once_with("avatar-id")
        self.mock_comment_service.mask_comments_by_account_id.assert_called_once_with(1)
        self.mock_repo.delete.assert_called_once_with(1)

    def test_delete_account_no_avatar_skips_cleanup(self):
        fake_account = create_test_account(account_id=1)
        self.mock_repo.get_by_id.return_value = fake_account

        self.service.delete_account(1)

        self.mock_file_service.delete_file.assert_not_called()
        self.mock_comment_service.mask_comments_by_account_id.assert_called_once_with(1)
        self.mock_repo.delete.assert_called_once_with(1)

    def test_delete_account_avatar_error_continues_cascade(self):
        fake_account = create_test_account(account_id=1, account_avatar_file_id="av-id")
        self.mock_repo.get_by_id.return_value = fake_account
        self.mock_file_service.delete_file.side_effect = BlogCommentError("Storage fail")

        self.service.delete_account(1)

        self.mock_file_service.delete_file.assert_called_once_with("av-id")
        self.mock_comment_service.mask_comments_by_account_id.assert_called_once_with(1)
        self.mock_repo.delete.assert_called_once_with(1)

    def test_change_role_success(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target}.get(cid)

        result = self.service.update_account_role(
            admin_id=1, target_id=2, new_role="author"
        )

        assert result is None
        self.mock_repo.update_role.assert_called_once_with(2, "author")

    def test_change_role_account_not_found(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin}.get(cid)

        with pytest.raises(AccountNotFoundError, match="not found"):
            self.service.update_account_role(
                admin_id=1, target_id=999, new_role="author"
            )

        self.mock_repo.update_role.assert_not_called()

    def test_change_role_not_admin(self):
        user = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.return_value = user

        with pytest.raises(AuthorizationError, match="Unauthorized"):
            self.service.update_account_role(
                admin_id=1, target_id=2, new_role="author"
            )

        self.mock_repo.update_role.assert_not_called()

    def test_change_role_target_is_admin(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target_admin = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target_admin}.get(cid)

        with pytest.raises(AuthorizationError, match="Cannot change"):
            self.service.update_account_role(
                admin_id=1, target_id=2, new_role="user"
            )

        self.mock_repo.update_role.assert_not_called()

    def test_change_role_invalid_role(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target}.get(cid)

        result = self.service.update_account_role(
            admin_id=1, target_id=2, new_role="superadmin"
        )

        assert result is None
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

        with pytest.raises(AccountNotFoundError, match="not found"):
            self.service.ban_account(admin_id=1, target_account_id=999, ban_reason="Spam")

        self.mock_repo.update_ban_status.assert_not_called()

    def test_ban_account_target_is_admin(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target_admin = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target_admin}.get(cid)

        with pytest.raises(AuthorizationError, match="ban another administrator"):
            self.service.ban_account(admin_id=1, target_account_id=2, ban_reason="Spam")

        self.mock_repo.update_ban_status.assert_not_called()

    def test_ban_account_clears_session_token(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target}.get(cid)

        self.service.ban_account(admin_id=1, target_account_id=2, ban_reason="Spam")

        self.mock_repo.update_ban_status.assert_called_once_with(2, True, "Spam")
        self.mock_repo.update_session_token.assert_called_once_with(2, None)

    def test_unban_account_success(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_repo.get_by_id.side_effect = lambda cid: {1: admin, 2: target}.get(cid)

        result = self.service.unban_account(admin_id=1, target_account_id=2)

        assert result is None
        self.mock_repo.update_ban_status.assert_called_once_with(2, False, None)
