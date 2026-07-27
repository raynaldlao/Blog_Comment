from unittest.mock import MagicMock

import pytest

from blog_exceptions import (
    AccountNotFoundError,
    ArticleNotFoundError,
    CommentAuthorizationError,
    CommentDeletedError,
    CommentNotFoundError,
    CommentValidationError,
)
from src.application.domain.account import AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.output_ports.comment_repository import CommentRepository
from src.application.services.comment_service import CommentService
from tests.test_domain_factories import (
    create_test_account,
    create_test_article,
    create_test_comment,
)


class CommentServiceTestBase:
    def setup_method(self):
        self.mock_comment_repo = MagicMock(spec=CommentRepository, autospec=True)
        self.mock_article_repo = MagicMock(spec=ArticleRepository, autospec=True)
        self.mock_account_repo = MagicMock(spec=AccountRepository, autospec=True)

        self.service = CommentService(
            comment_repository=self.mock_comment_repo,
            article_repository=self.mock_article_repo,
            account_repository=self.mock_account_repo
        )


class TestCreateComment(CommentServiceTestBase):
    def test_create_comment_success(self):
        fake_account = create_test_account(account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        fake_article = create_test_article(article_id=1, article_author_id=2)
        self.mock_article_repo.get_by_id.return_value = fake_article

        result = self.service.create_comment(
            article_id=fake_article.article_id,
            user_id=fake_account.account_id,
            content="Great post!"
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_comment_repo.save.assert_called_once()
        saved_comment = self.mock_comment_repo.save.call_args.args[0]
        assert saved_comment.comment_article_id == fake_article.article_id
        assert saved_comment.comment_written_account_id == fake_account.account_id
        assert saved_comment.comment_reply_to is None
        assert saved_comment.comment_content == "Great post!"
        assert result is saved_comment

    def test_create_comment_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None

        with pytest.raises(AccountNotFoundError, match="not found"):
            self.service.create_comment(
                article_id=1,
                user_id=999,
                content="This will not post."
            )

        self.mock_account_repo.get_by_id.assert_called_once_with(999)
        self.mock_article_repo.get_by_id.assert_not_called()
        self.mock_comment_repo.save.assert_not_called()

    def test_create_comment_sanitizes_html(self):
        fake_account = create_test_account(account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        fake_article = create_test_article(article_id=1, article_author_id=2)
        self.mock_article_repo.get_by_id.return_value = fake_article

        malicious_content = '<script>alert("xss")</script><b>bold</b><a href="https://example.com" target="_blank">link</a>'
        result = self.service.create_comment(
            article_id=fake_article.article_id,
            user_id=fake_account.account_id,
            content=malicious_content,
        )

        saved_comment = self.mock_comment_repo.save.call_args.args[0]
        assert (
            saved_comment.comment_content
            == '<b>bold</b><a href="https://example.com" target="_blank" rel="noopener noreferrer">link</a>'
        )
        assert result is saved_comment

    def test_create_comment_article_not_found(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        self.mock_article_repo.get_by_id.return_value = None

        with pytest.raises(ArticleNotFoundError, match="not found"):
            self.service.create_comment(
                article_id=999,
                user_id=fake_account.account_id,
                content="Writing in the void."
            )

        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.save.assert_not_called()


class TestCreateReply(CommentServiceTestBase):
    def test_create_reply_success_root_comment(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account

        parent_comment = create_test_comment(
            comment_id=10,
            comment_article_id=5,
            comment_written_account_id=2,
            comment_reply_to=None,
            comment_content="Root comment",
        )

        self.mock_comment_repo.get_by_id.side_effect = lambda cid: parent_comment if cid == 10 else None

        result = self.service.create_reply(
            parent_comment_id=parent_comment.comment_id,
            user_id=fake_account.account_id, content="This is a reply"
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_comment_repo.get_by_id.assert_any_call(parent_comment.comment_id)
        self.mock_comment_repo.save.assert_called_once()
        saved_reply = self.mock_comment_repo.save.call_args.args[0]
        assert saved_reply.comment_article_id == parent_comment.comment_article_id
        assert saved_reply.comment_written_account_id == fake_account.account_id
        assert saved_reply.comment_reply_to == parent_comment.comment_id
        assert saved_reply.comment_content == "This is a reply"
        assert result is saved_reply

    def test_create_reply_success_nested_comment(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account

        root_comment = create_test_comment(
            comment_id=10,
            comment_reply_to=None,
        )
        parent_comment = create_test_comment(
            comment_id=15,
            comment_article_id=5,
            comment_written_account_id=2,
            comment_reply_to=10,
            comment_content="I am a reply",
        )

        def mock_get_by_id(cid):
            mapping = {10: root_comment, 15: parent_comment}
            return mapping.get(cid)

        self.mock_comment_repo.get_by_id.side_effect = mock_get_by_id

        result = self.service.create_reply(
            parent_comment_id=parent_comment.comment_id,
            user_id=fake_account.account_id, content="Replying to a reply"
        )

        self.mock_comment_repo.save.assert_called_once()
        saved_reply = self.mock_comment_repo.save.call_args.args[0]
        assert saved_reply.comment_reply_to == parent_comment.comment_id
        assert result is saved_reply

    def test_create_reply_parent_not_found(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        self.mock_comment_repo.get_by_id.return_value = None

        with pytest.raises(CommentNotFoundError, match="not found"):
            self.service.create_reply(
                parent_comment_id=999,
                user_id=fake_account.account_id,
                content="Replying to nothing"
            )

        self.mock_comment_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.save.assert_not_called()

    def test_create_reply_to_deleted_comment_returns_error(self):
        self.mock_account_repo.get_by_id.return_value = create_test_account(
            account_id=99, account_role=AccountRole.ADMIN
        )

        deleted = create_test_comment(
            comment_id=5,
            comment_content="Original content",
            is_deleted=True,
        )

        self.mock_comment_repo.get_by_id.return_value = deleted

        with pytest.raises(CommentDeletedError, match="deleted"):
            self.service.create_reply(5, 99, "Reply to deleted")

        self.mock_comment_repo.save.assert_not_called()

    def test_create_reply_too_deep_returns_error(self):
        self.mock_account_repo.get_by_id.return_value = create_test_account(
            account_id=1, account_role=AccountRole.USER
        )
        deep_comment_1 = create_test_comment(comment_id=1, comment_reply_to=None)
        deep_comment_2 = create_test_comment(comment_id=2, comment_reply_to=1)
        deep_comment_3 = create_test_comment(comment_id=3, comment_reply_to=2)
        deep_parent = create_test_comment(comment_id=4, comment_reply_to=3)

        def mock_get_by_id(cid):
            mapping = {1: deep_comment_1, 2: deep_comment_2, 3: deep_comment_3, 4: deep_parent}
            return mapping.get(cid)

        self.mock_comment_repo.get_by_id.side_effect = mock_get_by_id

        with pytest.raises(CommentValidationError, match="maximum depth"):
            self.service.create_reply(4, 1, "Too deep reply")

        self.mock_comment_repo.save.assert_not_called()


class TestDeleteComment(CommentServiceTestBase):
    def test_delete_comment_soft_delete_by_author(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        comment_to_delete = create_test_comment(
            comment_id=10,
            comment_written_account_id=1,
            comment_content="Original content",
        )
        self.mock_comment_repo.get_by_id.return_value = comment_to_delete

        result = self.service.delete_comment(
            comment_id=comment_to_delete.comment_id,
            user_id=fake_account.account_id,
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_comment_repo.get_by_id.assert_called_once_with(comment_to_delete.comment_id)
        self.mock_comment_repo.save.assert_called_once()
        assert result is True
        assert comment_to_delete.is_deleted is True
        assert comment_to_delete.deleted_at is not None
        assert comment_to_delete.comment_content == "Original content"
        assert comment_to_delete.deleted_by == "user"

    def test_delete_comment_soft_delete_by_admin(self):
        admin_account = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_account_repo.get_by_id.return_value = admin_account
        comment_to_delete = create_test_comment(
            comment_id=10,
            comment_written_account_id=1,
            comment_content="Original content",
        )
        self.mock_comment_repo.get_by_id.return_value = comment_to_delete

        result = self.service.delete_comment(
            comment_id=comment_to_delete.comment_id,
            user_id=admin_account.account_id,
        )

        self.mock_comment_repo.save.assert_called_once()
        assert result is True
        assert comment_to_delete.is_deleted is True
        assert comment_to_delete.deleted_by == "admin"

    def test_delete_comment_unauthorized_not_author(self):
        fake_account = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        comment = create_test_comment(comment_id=10, comment_written_account_id=1)
        self.mock_comment_repo.get_by_id.return_value = comment

        with pytest.raises(CommentAuthorizationError, match="own comments"):
            self.service.delete_comment(comment_id=10, user_id=fake_account.account_id)

        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_comment_repo.get_by_id.assert_called_once()
        self.mock_comment_repo.save.assert_not_called()

    def test_delete_comment_not_found(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        self.mock_comment_repo.get_by_id.return_value = None

        with pytest.raises(CommentNotFoundError, match="not found"):
            self.service.delete_comment(comment_id=999, user_id=fake_account.account_id)

        self.mock_comment_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.save.assert_not_called()

    def test_delete_comment_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None

        with pytest.raises(AccountNotFoundError, match="not found"):
            self.service.delete_comment(comment_id=10, user_id=999)

        self.mock_account_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.get_by_id.assert_not_called()
        self.mock_comment_repo.save.assert_not_called()

    def test_delete_comment_already_deleted_idempotent(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        comment = create_test_comment(
            comment_id=10,
            comment_written_account_id=1,
            is_deleted=True,
        )
        self.mock_comment_repo.get_by_id.return_value = comment
        result = self.service.delete_comment(comment_id=10, user_id=fake_account.account_id)
        self.mock_comment_repo.save.assert_not_called()
        assert result is True


class TestEditComment(CommentServiceTestBase):
    def test_edit_comment_success(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        comment = create_test_comment(
            comment_id=10,
            comment_written_account_id=1,
            comment_content="Original",
        )
        self.mock_comment_repo.get_by_id.return_value = comment

        result = self.service.edit_comment(
            comment_id=10,
            user_id=fake_account.account_id,
            content="Updated content",
        )

        self.mock_comment_repo.save.assert_called_once()
        assert isinstance(result, type(comment))
        assert result.comment_content == "Updated content"
        assert result.edited_at is not None

    def test_edit_comment_not_author(self):
        fake_account = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        comment = create_test_comment(comment_id=10, comment_written_account_id=1)
        self.mock_comment_repo.get_by_id.return_value = comment

        with pytest.raises(CommentAuthorizationError, match="own comments"):
            self.service.edit_comment(comment_id=10, user_id=2, content="Hack")

        self.mock_comment_repo.save.assert_not_called()

    def test_edit_comment_deleted(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        comment = create_test_comment(
            comment_id=10,
            comment_written_account_id=1,
            is_deleted=True,
        )
        self.mock_comment_repo.get_by_id.return_value = comment

        with pytest.raises(CommentDeletedError, match="deleted"):
            self.service.edit_comment(comment_id=10, user_id=1, content="New")

        self.mock_comment_repo.save.assert_not_called()

    def test_edit_comment_not_found(self):
        fake_account = create_test_account(account_id=1)
        self.mock_account_repo.get_by_id.return_value = fake_account
        self.mock_comment_repo.get_by_id.return_value = None

        with pytest.raises(CommentNotFoundError, match="not found"):
            self.service.edit_comment(comment_id=999, user_id=1, content="X")

        self.mock_comment_repo.save.assert_not_called()

    def test_edit_comment_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None

        with pytest.raises(AccountNotFoundError, match="not found"):
            self.service.edit_comment(comment_id=10, user_id=999, content="X")

        self.mock_comment_repo.save.assert_not_called()


class TestMaskCommentsByAccountId(CommentServiceTestBase):
    def test_mask_comments_success(self):
        target_id = 5
        c1 = create_test_comment(comment_id=1, comment_written_account_id=target_id, comment_content="Hello")
        c2 = create_test_comment(comment_id=2, comment_written_account_id=target_id, comment_content="World")
        self.mock_comment_repo.get_by_account_id.return_value = [c1, c2]

        self.service.mask_comments_by_account_id(target_id)

        self.mock_comment_repo.get_by_account_id.assert_called_once_with(target_id)
        assert self.mock_comment_repo.save.call_count == 2
        assert c1.comment_content == "<!--cmt-removed--><em>Comment removed</em>"
        assert c2.comment_content == "<!--cmt-removed--><em>Comment removed</em>"
        assert c1.is_deleted is True
        assert c1.deleted_at is not None
        assert c1.deleted_by == "account_deleted"
        assert c2.deleted_by == "account_deleted"

    def test_mask_comments_no_comments(self):
        self.mock_comment_repo.get_by_account_id.return_value = []
        self.service.mask_comments_by_account_id(999)
        self.mock_comment_repo.get_by_account_id.assert_called_once_with(999)
        self.mock_comment_repo.save.assert_not_called()


class TestHardDeleteComment(CommentServiceTestBase):
    def test_hard_delete_comment_by_admin(self):
        admin = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_account_repo.get_by_id.return_value = admin
        comment = create_test_comment(
            comment_id=10,
            comment_written_account_id=1,
            is_deleted=True,
        )
        self.mock_comment_repo.get_by_id.return_value = comment

        result = self.service.hard_delete_comment(
            comment_id=10,
            user_id=admin.account_id,
        )

        self.mock_comment_repo.delete.assert_called_once_with(10)
        assert result is True

    def test_hard_delete_comment_not_admin(self):
        user = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = user

        with pytest.raises(CommentAuthorizationError, match="administrators"):
            self.service.hard_delete_comment(comment_id=10, user_id=1)

        self.mock_comment_repo.delete.assert_not_called()

    def test_hard_delete_comment_not_found(self):
        admin = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_account_repo.get_by_id.return_value = admin
        self.mock_comment_repo.get_by_id.return_value = None

        with pytest.raises(CommentNotFoundError, match="not found"):
            self.service.hard_delete_comment(comment_id=999, user_id=2)

        self.mock_comment_repo.delete.assert_not_called()

    def test_hard_delete_comment_not_soft_deleted(self):
        admin = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_account_repo.get_by_id.return_value = admin
        comment = create_test_comment(
            comment_id=10,
            comment_written_account_id=1,
            is_deleted=False,
        )
        self.mock_comment_repo.get_by_id.return_value = comment

        with pytest.raises(CommentValidationError, match="not deleted"):
            self.service.hard_delete_comment(comment_id=10, user_id=2)

        self.mock_comment_repo.delete.assert_not_called()

    def test_hard_delete_comment_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None

        with pytest.raises(AccountNotFoundError, match="not found"):
            self.service.hard_delete_comment(comment_id=10, user_id=999)

        self.mock_comment_repo.delete.assert_not_called()


class TestCheckRateLimit(CommentServiceTestBase):
    def test_first_comment_allowed(self):
        result = self.service.check_rate_limit(user_id=1)
        assert result is None

    def test_second_comment_within_interval_blocked(self):
        self.service.check_rate_limit(user_id=1)
        result = self.service.check_rate_limit(user_id=1)
        assert result is not None
        assert isinstance(result, int)
        assert result > 0

    def test_different_users_independent(self):
        self.service.check_rate_limit(user_id=1)
        result = self.service.check_rate_limit(user_id=2)
        assert result is None

    def test_called_once_increments_timestamp_dict(self):
        assert len(self.service._user_comment_timestamps) == 0
        self.service.check_rate_limit(user_id=1)
        assert len(self.service._user_comment_timestamps) == 1
