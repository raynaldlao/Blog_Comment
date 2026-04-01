from unittest.mock import MagicMock

from src.application.domain.account import AccountRole
from src.application.output_ports.account_repository import AccountRepository
from src.application.output_ports.article_repository import ArticleRepository
from src.application.output_ports.comment_repository import CommentRepository
from src.application.services.comment_service import CommentService
from tests_hexagonal.test_domain_factories import (
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

        self.mock_comment_repo.get_by_id.return_value = parent_comment

        result = self.service.create_reply(
            parent_comment_id=parent_comment.comment_id,
            user_id=fake_account.account_id, content="This is a reply"
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_comment_repo.get_by_id.assert_called_once_with(parent_comment.comment_id)
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

        parent_comment = create_test_comment(
            comment_id=15,
            comment_article_id=5,
            comment_written_account_id=2,
            comment_reply_to=10,
            comment_content="I am a reply",
        )
        self.mock_comment_repo.get_by_id.return_value = parent_comment

        result = self.service.create_reply(
            parent_comment_id=parent_comment.comment_id,
            user_id=fake_account.account_id, content="Replying to a reply"
        )

        self.mock_comment_repo.save.assert_called_once()
        index_first_arg = 0
        saved_reply = self.mock_comment_repo.save.call_args.args[index_first_arg]
        assert saved_reply.comment_reply_to == 10
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
        result = self.service.get_comments_for_article(article_id=fake_article.article_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_comment_repo.get_all_by_article_id.assert_called_once_with(fake_article.article_id)
        assert result == {"root": []}

    def test_get_comments_for_article_success(self):
        fake_article = create_test_article(article_id=1, article_author_id=2)
        self.mock_article_repo.get_by_id.return_value = fake_article

        root_comment = create_test_comment(
            comment_id=10,
            comment_article_id=fake_article.article_id,
            comment_written_account_id=3,
            comment_reply_to=None,
            comment_content="First!",
        )

        reply = create_test_comment(
            comment_id=15,
            comment_article_id=fake_article.article_id,
            comment_written_account_id=4,
            comment_reply_to=root_comment.comment_id,
            comment_content="Awesome!",
        )

        self.mock_comment_repo.get_all_by_article_id.return_value = [root_comment, reply]
        result = self.service.get_comments_for_article(article_id=fake_article.article_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_comment_repo.get_all_by_article_id.assert_called_once_with(fake_article.article_id)
        assert result["root"] == [root_comment]
        assert result[root_comment.comment_id] == [reply]


class TestDeleteComment(CommentServiceTestBase):
    def test_delete_comment_success_as_admin(self):
        admin_account = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.mock_account_repo.get_by_id.return_value = admin_account

        comment_to_delete = create_test_comment(comment_id=10, comment_written_account_id=2)
        self.mock_comment_repo.get_by_id.return_value = comment_to_delete

        result = self.service.delete_comment(
            comment_id=comment_to_delete.comment_id,
            user_id=admin_account.account_id
        )

        self.mock_account_repo.get_by_id.assert_called_once_with(admin_account.account_id)
        self.mock_comment_repo.get_by_id.assert_called_once_with(comment_to_delete.comment_id)
        self.mock_comment_repo.delete.assert_called_once_with(comment_to_delete.comment_id)
        assert result is True

    def test_delete_comment_unauthorized_not_admin(self):
        fake_account = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.mock_account_repo.get_by_id.return_value = fake_account
        result = self.service.delete_comment(comment_id=10, user_id=fake_account.account_id)
        self.mock_account_repo.get_by_id.assert_called_once_with(fake_account.account_id)
        self.mock_comment_repo.get_by_id.assert_not_called()
        self.mock_comment_repo.delete.assert_not_called()
        assert result == "Unauthorized : Only admins can delete comments."

    def test_delete_comment_not_found(self):
        fake_account = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.mock_account_repo.get_by_id.return_value = fake_account
        self.mock_comment_repo.get_by_id.return_value = None
        result = self.service.delete_comment(comment_id=999, user_id=fake_account.account_id)
        self.mock_comment_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.delete.assert_not_called()
        assert result == "Comment not found."

    def test_delete_comment_account_not_found(self):
        self.mock_account_repo.get_by_id.return_value = None
        result = self.service.delete_comment(comment_id=10, user_id=999)
        self.mock_account_repo.get_by_id.assert_called_once_with(999)
        self.mock_comment_repo.get_by_id.assert_not_called()
        self.mock_comment_repo.delete.assert_not_called()
        assert result == "Account not found."
