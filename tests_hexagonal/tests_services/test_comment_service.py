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
        self.mock_account_repo.get_by_ids.return_value = []
        comments = self.service.get_comments_for_article(article_id=fake_article.article_id)
        self.mock_article_repo.get_by_id.assert_called_once_with(fake_article.article_id)
        self.mock_comment_repo.get_all_by_article_id.assert_called_once_with(fake_article.article_id)
        assert comments.threads == {"root": []}

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
        root_comment_view, = result.threads["root"]
        reply_view, = result.threads[root_comment.comment_id]
        assert root_comment_view.comment == root_comment
        assert root_comment_view.author_name == "Author3"
        assert reply_view.comment == reply
        assert reply_view.author_name == "Author4"

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
        latest_root, oldest_root = result.threads["root"]
        latest_reply, oldest_reply = result.threads[comment_2.comment_id]
        assert latest_root.comment.comment_id == comment_2.comment_id
        assert oldest_root.comment.comment_id == comment_1.comment_id
        assert latest_reply.comment.comment_id == reply_2.comment_id
        assert oldest_reply.comment.comment_id == reply_1.comment_id

    def test_get_comments_for_article_unknown_author(self):
        fake_article = create_test_article(article_id=1, article_author_id=2)
        self.mock_article_repo.get_by_id.return_value = fake_article
        comment = create_test_comment(comment_id=1, comment_written_account_id=999, comment_reply_to=None)
        self.mock_comment_repo.get_all_by_article_id.return_value = [comment]
        self.mock_account_repo.get_by_ids.return_value = []
        result = self.service.get_comments_for_article(article_id=1)
        comment_view, = result.threads["root"]
        assert comment_view.author_name == "Unknown"


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
