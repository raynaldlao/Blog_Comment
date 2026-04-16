from unittest.mock import Mock

from src.application.domain.account import AccountRole
from src.application.input_ports.comment_management import CommentManagementPort
from src.infrastructure.input_adapters.flask.flask_comment_adapter import CommentAdapter
from tests_hexagonal.test_domain_factories import create_test_account
from tests_hexagonal.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class CommentAdapterTestBase(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_comment_service = Mock(spec=CommentManagementPort, autospec=True)
        self.adapter = CommentAdapter(comment_service=self.mock_comment_service)

        self.app.add_url_rule(
            "/articles/<int:article_id>/comments",
            view_func=self.adapter.create_comment,
            methods=["POST"],
            endpoint="comment.create_comment"
        )

        self.app.add_url_rule(
            "/articles/<int:article_id>/comments/<int:parent_comment_id>/reply",
            view_func=self.adapter.reply_to_comment,
            methods=["POST"],
            endpoint="comment.reply_to_comment"
        )

        self.app.add_url_rule(
            "/articles/<int:article_id>/comments/<int:comment_id>/delete",
            view_func=self.adapter.delete_comment,
            methods=["POST"],
            endpoint="comment.delete_comment"
        )

        self._register_dummy_route("/login", "auth.login")
        self._register_dummy_route("/articles/<int:article_id>", "article.read_article")

class TestCommentCreate(CommentAdapterTestBase):
    def test_create_comment_requires_login(self):
        response = self.client.post("/articles/1/comments", data={"content": "Some text"})
        assert response.status_code == 302
        assert response.location.endswith("/login")
        self.mock_comment_service.create_comment.assert_not_called()

    def test_create_comment_success_and_redirects(self):
        user = create_test_account(account_id=123)
        self.set_current_user(user)
        self.mock_comment_service.create_comment.return_value = Mock()
        response = self.client.post("/articles/1/comments", data={"content": "Hello!"})
        assert response.status_code == 302
        assert response.location.endswith("/articles/1")

        self.mock_comment_service.create_comment.assert_called_once_with(
            article_id=1,
            user_id=123,
            content="Hello!"
        )

    def test_create_comment_validation_error(self):
        user = create_test_account(account_id=123)
        self.set_current_user(user)
        response = self.client.post("/articles/1/comments", data={"content": ""}, follow_redirects=True)
        assert b"Validation Error" in response.data

    def test_create_comment_service_error_string(self):
        user = create_test_account(account_id=123)
        self.set_current_user(user)
        self.mock_comment_service.create_comment.return_value = "Article not found"
        response = self.client.post("/articles/1/comments", data={"content": "Valid"}, follow_redirects=True)
        assert b"Article not found" in response.data

class TestCommentReply(CommentAdapterTestBase):
    def test_reply_to_comment_success(self):
        user = create_test_account(account_id=456)
        self.set_current_user(user)
        self.mock_comment_service.create_reply.return_value = Mock()
        response = self.client.post("/articles/1/comments/10/reply", data={"content": "Nice reply"})
        assert response.status_code == 302
        assert response.location.endswith("/articles/1")

        self.mock_comment_service.create_reply.assert_called_once_with(
            parent_comment_id=10,
            user_id=456,
            content="Nice reply"
        )

    def test_reply_requires_login(self):
        response = self.client.post("/articles/1/comments/10/reply", data={"content": "T"}, follow_redirects=True)
        assert b"You must be signed in to reply" in response.data

    def test_reply_validation_error(self):
        user = create_test_account(account_id=123)
        self.set_current_user(user)
        response = self.client.post("/articles/1/comments/10/reply", data={"content": ""}, follow_redirects=True)
        assert b"Validation Error" in response.data

    def test_reply_service_error_string(self):
        user = create_test_account(account_id=123)
        self.set_current_user(user)
        self.mock_comment_service.create_reply.return_value = "Parent not found"
        response = self.client.post("/articles/1/comments/10/reply", data={"content": "Valid"}, follow_redirects=True)
        assert b"Parent not found" in response.data

class TestCommentDelete(CommentAdapterTestBase):
    def test_delete_comment_success(self):
        user = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(user)
        self.mock_comment_service.delete_comment.return_value = True
        response = self.client.post("/articles/1/comments/99/delete")
        assert response.status_code == 302
        assert response.location.endswith("/articles/1")

        self.mock_comment_service.delete_comment.assert_called_once_with(
            comment_id=99,
            user_id=1
        )

    def test_delete_comment_requires_login(self):
        response = self.client.post("/articles/1/comments/99/delete", follow_redirects=True)
        assert b"You must be signed in to delete comments" in response.data

    def test_delete_comment_service_error_string(self):
        user = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(user)
        self.mock_comment_service.delete_comment.return_value = "Comment not found"
        response = self.client.post("/articles/1/comments/99/delete", follow_redirects=True)
        assert b"Comment not found" in response.data

    def test_delete_comment_unauthorized_none_return(self):
        user = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(user)
        self.mock_comment_service.delete_comment.return_value = None
        response = self.client.post("/articles/1/comments/99/delete", follow_redirects=True)
        assert b"Unauthorized or error" in response.data
