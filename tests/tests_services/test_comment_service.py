from unittest.mock import MagicMock

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
        index_first_arg = 0
        saved_comment = self.mock_comment_repo.save.call_args.args[index_first_arg]
        assert saved_comment.comment_article_id == fake_article.article_id
        assert saved_comment.comment_written_account_id == fake_account.account_id
        assert saved_comment.comment_reply_to is None
        assert saved_comment.comment_content == "Great post!"
        assert result is saved_comment

    def test_create_comment_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None

        result = self.service.create_comment(
            article_id=1,
            user_id=999,
            content="This will not post."
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(999)
        self.mock_article_repo.get_by_id.assert_not_called()
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Account not found."

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

        result = self.service.create_comment(
            article_id=999,
            user_id=fake_account.account_id,
            content="Writing in the void."
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Article not found."


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
        index_first_arg = 0
        saved_reply = self.mock_comment_repo.save.call_args.args[index_first_arg]
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
        index_first_arg = 0
        saved_reply = self.mock_comment_repo.save.call_args.args[index_first_arg]
        assert saved_reply.comment_reply_to == parent_comment.comment_id
        assert result is saved_reply

    def test_create_reply_parent_not_found(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        self.mock_comment_repo.get_by_id.return_value = None

        result = self.service.create_reply(
            parent_comment_id=999,
            user_id=fake_account.account_id,
            content="Replying to nothing"
        )

        self.mock_comment_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Parent comment not found."

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
        result = self.service.create_reply(5, 99, "Reply to deleted")
        self.mock_comment_repo.save.assert_not_called()
        assert isinstance(result, str)
        assert "deleted" in result.lower()

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

        result = self.service.create_reply(4, 1, "Too deep reply")
        self.mock_comment_repo.save.assert_not_called()
        assert isinstance(result, str)
        assert "maximum nesting depth" in result.lower()


class TestGetComments(CommentServiceTestBase):
    def test_get_comments_for_article_not_found(self):
        self.mock_article_repo.get_by_id.return_value = None
        result = self.service.get_comments_for_article(article_id=999)
        self.mock_article_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.get_all_by_article_id.assert_not_called()
        assert result == "Article not found."

    def test_get_comments_for_article_empty(self):
        fake_article = create_test_article(article_id=1, article_author_id=2)
        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_comment_repo.get_all_by_article_id.return_value = []
        self.mock_account_repo.get_by_ids.return_value = []
        comments = self.service.get_comments_for_article(article_id=fake_article.article_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_comment_repo.get_all_by_article_id.assert_called_once_with(fake_article.article_id)
        assert not isinstance(comments, str)
        assert comments == []

    def test_get_comments_for_article_success(self):
        fake_article = create_test_article(article_id=1, article_author_id=2)
        self.mock_article_repo.get_by_id.return_value = fake_article
        root_author_id = 3
        reply_author_id = 4

        root_comment = create_test_comment(
            comment_id=10,
            comment_article_id=fake_article.article_id,
            comment_written_account_id=root_author_id,
            comment_reply_to=None,
            comment_content="First!",
        )

        reply = create_test_comment(
            comment_id=15,
            comment_article_id=fake_article.article_id,
            comment_written_account_id=reply_author_id,
            comment_reply_to=root_comment.comment_id,
            comment_content="Awesome!",
        )

        self.mock_comment_repo.get_all_by_article_id.return_value = [root_comment, reply]

        self.mock_account_repo.get_by_ids.return_value = [
            create_test_account(account_id=root_author_id, account_username="Author3"),
            create_test_account(account_id=reply_author_id, account_username="Author4")
        ]

        result = self.service.get_comments_for_article(article_id=fake_article.article_id)
        assert not isinstance(result, str)
        root_node, = result
        reply_node, = root_node.replies
        assert root_node.comment.comment == root_comment
        assert root_node.comment.author_name == "Author3"
        assert reply_node.comment.comment == reply
        assert reply_node.comment.author_name == "Author4"

    def test_get_comments_for_article_ordering(self):
        from datetime import datetime
        fake_article = create_test_article(article_id=1, article_author_id=2)
        self.mock_article_repo.get_by_id.return_value = fake_article
        self.mock_account_repo.get_by_ids.return_value = []
        comment_1 = create_test_comment(comment_id=1, comment_posted_at=datetime(2026, 1, 1), comment_reply_to=None)
        comment_2 = create_test_comment(comment_id=2, comment_posted_at=datetime(2026, 1, 2), comment_reply_to=None)
        reply_1 = create_test_comment(comment_id=3, comment_posted_at=datetime(2026, 1, 4), comment_reply_to=2)
        reply_2 = create_test_comment(comment_id=4, comment_posted_at=datetime(2026, 1, 3), comment_reply_to=2)
        self.mock_comment_repo.get_all_by_article_id.return_value = [comment_1, comment_2, reply_1, reply_2]
        result = self.service.get_comments_for_article(article_id=1)
        assert not isinstance(result, str)
        latest_root, oldest_root = result
        latest_reply, oldest_reply = result[0].replies
        assert latest_root.comment.comment.comment_id == comment_2.comment_id
        assert oldest_root.comment.comment.comment_id == comment_1.comment_id
        assert latest_reply.comment.comment.comment_id == reply_1.comment_id
        assert oldest_reply.comment.comment.comment_id == reply_2.comment_id

    def test_get_comments_for_article_unknown_author(self):
        fake_article = create_test_article(article_id=1, article_author_id=2)
        self.mock_article_repo.get_by_id.return_value = fake_article
        comment = create_test_comment(comment_id=1, comment_written_account_id=999, comment_reply_to=None)
        self.mock_comment_repo.get_all_by_article_id.return_value = [comment]
        self.mock_account_repo.get_by_ids.return_value = []
        result = self.service.get_comments_for_article(article_id=1)
        assert not isinstance(result, str)
        comment_node, = result
        assert comment_node.comment.author_name == "Anonymous"


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

    def test_delete_comment_unauthorized_not_author(self):
        fake_account = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        comment = create_test_comment(comment_id=10, comment_written_account_id=1)
        self.mock_comment_repo.get_by_id.return_value = comment
        result = self.service.delete_comment(comment_id=10, user_id=fake_account.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_comment_repo.get_by_id.assert_called_once()
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Unauthorized: You can only delete your own comments."

    def test_delete_comment_not_found(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        self.mock_comment_repo.get_by_id.return_value = None
        result = self.service.delete_comment(comment_id=999, user_id=fake_account.account_id)
        self.mock_comment_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Comment not found."

    def test_delete_comment_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None
        result = self.service.delete_comment(comment_id=10, user_id=999)
        self.mock_account_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.get_by_id.assert_not_called()
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Account not found."

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
        result = self.service.edit_comment(comment_id=10, user_id=2, content="Hack")
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Unauthorized: You can only edit your own comments."

    def test_edit_comment_deleted(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        comment = create_test_comment(
            comment_id=10,
            comment_written_account_id=1,
            is_deleted=True,
        )
        self.mock_comment_repo.get_by_id.return_value = comment
        result = self.service.edit_comment(comment_id=10, user_id=1, content="New")
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Cannot edit a deleted comment."

    def test_edit_comment_not_found(self):
        fake_account = create_test_account(account_id=1)
        self.mock_account_repo.get_by_id.return_value = fake_account
        self.mock_comment_repo.get_by_id.return_value = None
        result = self.service.edit_comment(comment_id=999, user_id=1, content="X")
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Comment not found."

    def test_edit_comment_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None
        result = self.service.edit_comment(comment_id=10, user_id=999, content="X")
        self.mock_comment_repo.save.assert_not_called()
        assert result == "Account not found."


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
        result = self.service.hard_delete_comment(comment_id=10, user_id=1)
        self.mock_comment_repo.delete.assert_not_called()
        assert result == "Unauthorized: Only admins can permanently delete comments."

    def test_hard_delete_comment_not_found(self):
        admin = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_account_repo.get_by_id.return_value = admin
        self.mock_comment_repo.get_by_id.return_value = None
        result = self.service.hard_delete_comment(comment_id=999, user_id=2)
        self.mock_comment_repo.delete.assert_not_called()
        assert result == "Comment not found."

    def test_hard_delete_comment_not_soft_deleted(self):
        admin = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.mock_account_repo.get_by_id.return_value = admin
        comment = create_test_comment(
            comment_id=10,
            comment_written_account_id=1,
            is_deleted=False,
        )
        self.mock_comment_repo.get_by_id.return_value = comment
        result = self.service.hard_delete_comment(comment_id=10, user_id=2)
        self.mock_comment_repo.delete.assert_not_called()
        assert result == "Comment is not soft-deleted. Use soft-delete first."

    def test_hard_delete_comment_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None
        result = self.service.hard_delete_comment(comment_id=10, user_id=999)
        self.mock_comment_repo.delete.assert_not_called()
        assert result == "Account not found."
