from unittest.mock import Mock

from flask import g as global_request_context

from src.application.domain.account import Account, AccountRole
from src.application.input_ports.account_session_management import AccountSessionManagementPort
from src.application.input_ports.file_management import FileManagementPort
from src.infrastructure.input_adapters.flask.flask_account_session_adapter import AccountSessionAdapter
from tests.test_domain_factories import create_test_account
from tests.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class TestAccountSessionAdapter(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_session_service = Mock(spec=AccountSessionManagementPort, autospec=True)
        self.mock_session_service.count_all_accounts.return_value = 0
        self.mock_session_service.search_accounts.return_value = []
        self.mock_session_service.count_search_accounts.return_value = 0
        self.mock_file_service = Mock(spec=FileManagementPort, autospec=True)
        self.adapter = AccountSessionAdapter(
            session_service=self.mock_session_service,
            file_service=self.mock_file_service,
        )

        self.app.add_url_rule(
            "/logout",
            view_func=self.adapter.logout,
            methods=["POST"],
            endpoint="auth.logout"
        )

        self.app.add_url_rule(
            "/profile",
            view_func=self.adapter.display_profile,
            endpoint="auth.profile"
        )

        self._register_dummy_route("/articles", "article.list_articles", "articles")
        self._register_dummy_route("/login", "auth.login", "login")
        self._register_dummy_route("/register", "registration.register", "registration")
        self._register_dummy_route("/articles/new", "article.render_create_page", "new_article")

        self.app.add_url_rule(
            "/account/delete",
            view_func=self.adapter.delete_account,
            methods=["POST"],
            endpoint="auth.delete_account",
        )

        self.app.add_url_rule(
            "/users/<username>",
            view_func=self.adapter.display_user_profile,
            endpoint="auth.user_profile",
        )

        self.app.add_url_rule(
            "/api/profile/photo",
            view_func=self.adapter.upload_profile_photo,
            methods=["POST"],
            endpoint="auth.upload_profile_photo",
        )

        self._register_dummy_route(
            "/uploads/<string:file_id>/<string:filename>",
            "file.serve_file",
            "file_serve",
        )

        self.app.add_url_rule(
            "/profile/photo/delete",
            view_func=self.adapter.remove_profile_photo,
            methods=["POST"],
            endpoint="auth.remove_profile_photo",
        )

        self.app.add_url_rule(
            "/profile/email",
            view_func=self.adapter.update_email,
            methods=["POST"],
            endpoint="auth.update_email",
        )

        self.app.add_url_rule(
            "/profile/password",
            view_func=self.adapter.update_password,
            methods=["POST"],
            endpoint="auth.update_password",
        )

        self.app.add_url_rule(
            "/admin/users",
            view_func=self.adapter.list_all_users,
            methods=["GET"],
            endpoint="auth.list_all_users",
        )

        self.app.add_url_rule(
            "/admin/users/<int:account_id>/role",
            view_func=self.adapter.change_role,
            methods=["POST"],
            endpoint="auth.change_role",
        )

    def test_logout_clears_session(self):
        response = self.client.post("/logout", follow_redirects=True)
        assert b"You have been logged out." in response.data
        assert b"alert-info" in response.data
        self.mock_session_service.terminate_session.assert_called_once()

    def test_logout_get_returns_method_not_allowed(self):
        response = self.client.get("/logout")
        assert response.status_code == 405

    def test_get_profile_success(self):
        fake_user = create_test_account()
        self.mock_session_service.get_current_account.return_value = fake_user
        response = self.client.get("/profile")
        assert response.status_code == 200
        assert b"leia" in response.data
        assert b"leia@galaxy.com" in response.data
        assert b"Profile" in response.data
        assert b"Logout" in response.data
        assert b"Sign In" not in response.data
        assert b"Sign Up" not in response.data
        self.mock_session_service.get_current_account.assert_called_once()

    def test_get_profile_author_nav(self):
        fake_author = create_test_account(account_role=AccountRole.AUTHOR)
        self.mock_session_service.get_current_account.return_value = fake_author
        response = self.client.get("/profile")
        assert response.status_code == 200
        assert b"New article" in response.data

    def test_get_profile_unauthenticated(self):
        self.mock_session_service.get_current_account.return_value = None
        response = self.client.get("/profile", follow_redirects=True)
        assert b"Please sign in to view your profile." in response.data
        assert b"alert-error" in response.data
        assert b"login" in response.data

    def test_get_user_profile_found(self):
        fake_user = create_test_account(account_username="yoda", account_email="yoda@dagobah.com")
        self.mock_session_service.get_account_by_username.return_value = fake_user
        response = self.client.get("/users/yoda")
        assert response.status_code == 200
        assert b"yoda" in response.data
        assert b"yoda@dagobah.com" not in response.data
        self.mock_session_service.get_account_by_username.assert_called_once_with("yoda")

    def test_get_user_profile_not_found(self):
        self.mock_session_service.get_account_by_username.return_value = None
        response = self.client.get("/users/nobody")
        assert response.status_code == 404

    def test_get_user_profile_own_profile(self):
        fake_user = create_test_account(account_username="luke", account_email="luke@tatooine.com")
        self.set_current_user(fake_user)
        self.mock_session_service.get_account_by_username.return_value = fake_user
        response = self.client.get("/users/luke")
        assert response.status_code == 200
        assert b"luke@tatooine.com" in response.data
        assert b"Sign Out" in response.data

    def test_get_user_profile_admin_view(self):
        profile_user = create_test_account(account_id=2, account_username="han", account_email="han@falcon.com")
        admin_user = create_test_account(account_id=99, account_username="admin", account_role=AccountRole.ADMIN)
        self.set_current_user(admin_user)
        self.mock_session_service.get_account_by_username.return_value = profile_user
        response = self.client.get("/users/han")
        assert response.status_code == 200
        assert b"han@falcon.com" in response.data
        assert b"Sign Out" not in response.data

    def test_get_user_profile_anonymous(self):
        fake_user = create_test_account(account_username="leia", account_email="leia@galaxy.com")
        self.mock_session_service.get_account_by_username.return_value = fake_user
        response = self.client.get("/users/leia")
        assert response.status_code == 200
        assert b"leia@galaxy.com" not in response.data
        assert b"Sign Out" not in response.data

    def test_upload_profile_photo_unauthenticated(self):
        response = self.client.post("/api/profile/photo")
        assert response.status_code == 401

    def test_upload_profile_photo_success(self):
        from datetime import datetime
        from io import BytesIO

        from src.application.domain.file_record import FileRecord

        fake_user = create_test_account()
        self.set_current_user(fake_user)
        fake_file = FileRecord(
            file_id="abc-123",
            original_filename="avatar.jpg",
            mime_type="image/jpeg",
            size=1024,
            data=b"fake-image-data",
            created_at=datetime.now(),
        )
        self.mock_file_service.upload_file.return_value = fake_file

        response = self.client.post(
            "/api/profile/photo",
            data={"file": (BytesIO(b"fake-image"), "avatar.jpg")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["avatar_url"] == "/uploads/abc-123/avatar"
        self.mock_file_service.upload_file.assert_called_once()
        self.mock_session_service.update_avatar.assert_called_once_with("abc-123")

    def test_upload_profile_photo_replaces_old_avatar(self):
        from datetime import datetime
        from io import BytesIO

        from src.application.domain.file_record import FileRecord

        fake_user = create_test_account(account_avatar_file_id="old-avatar-id")
        self.set_current_user(fake_user)
        fake_file = FileRecord(
            file_id="new-avatar-id",
            original_filename="new_avatar.jpg",
            mime_type="image/jpeg",
            size=1024,
            data=b"new-image-data",
            created_at=datetime.now(),
        )
        self.mock_file_service.upload_file.return_value = fake_file

        response = self.client.post(
            "/api/profile/photo",
            data={"file": (BytesIO(b"new-image"), "new_avatar.jpg")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        self.mock_file_service.delete_file.assert_called_once_with("old-avatar-id")
        self.mock_session_service.update_avatar.assert_called_once_with("new-avatar-id")

    def test_remove_profile_photo_unauthenticated(self):
        self.mock_session_service.get_current_account.return_value = None
        response = self.client.post("/profile/photo/delete", follow_redirects=True)
        assert b"Please sign in." in response.data
        assert b"alert-error" in response.data

    def test_remove_profile_photo_success(self):
        fake_user = create_test_account(account_avatar_file_id="abc-123")
        self.mock_session_service.get_current_account.return_value = fake_user
        response = self.client.post("/profile/photo/delete", follow_redirects=True)
        assert b"Profile photo removed." in response.data
        assert b"alert-success" in response.data
        self.mock_file_service.delete_file.assert_called_once_with("abc-123")
        self.mock_session_service.update_avatar.assert_called_once_with(None)

    def test_remove_profile_photo_no_avatar(self):
        fake_user = create_test_account(account_avatar_file_id=None)
        self.mock_session_service.get_current_account.return_value = fake_user
        response = self.client.post("/profile/photo/delete", follow_redirects=True)
        assert b"No avatar to remove." in response.data
        assert b"alert-error" in response.data

    def test_list_all_users_as_admin(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = fake_admin
        fake_users = [
            create_test_account(account_id=i, account_username=f"user{i}")
            for i in range(1, 26)
        ]
        self.mock_session_service.get_all_accounts.return_value = fake_users[:20]
        self.mock_session_service.count_all_accounts.return_value = 25

        response = self.client.get("/admin/users")
        assert response.status_code == 200
        assert b"user1" in response.data
        assert b"user20" in response.data
        assert b"Page 1 of 2" in response.data

    def test_list_all_users_page_2(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = fake_admin
        fake_users_page2 = [
            create_test_account(account_id=i, account_username=f"user{i}")
            for i in range(21, 26)
        ]
        self.mock_session_service.get_all_accounts.return_value = fake_users_page2
        self.mock_session_service.count_all_accounts.return_value = 25

        response = self.client.get("/admin/users?page=2")
        assert response.status_code == 200
        assert b"user21" in response.data
        assert b"user25" in response.data
        assert b"Page 2 of 2" in response.data

    def test_list_all_users_with_search(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = fake_admin
        fake_results = [
            create_test_account(account_id=i, account_username=f"user{i}")
            for i in range(1, 26)
        ]
        self.mock_session_service.search_accounts.return_value = fake_results[:20]
        self.mock_session_service.count_search_accounts.return_value = 25

        response = self.client.get("/admin/users?q=user")
        assert response.status_code == 200
        assert b"user1" in response.data
        assert b"user20" in response.data
        assert b"Page 1 of 2" in response.data
        self.mock_session_service.search_accounts.assert_called_once_with("user", page=1, per_page=20)
        self.mock_session_service.count_search_accounts.assert_called_once_with("user")

    def test_list_all_users_search_no_results(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = fake_admin

        response = self.client.get("/admin/users?q=zzz")
        assert response.status_code == 200
        assert b"Manage Users" in response.data
        self.mock_session_service.search_accounts.assert_called_once_with("zzz", page=1, per_page=20)
        self.mock_session_service.count_search_accounts.assert_called_once_with("zzz")

    def test_list_all_users_page_invalid(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = fake_admin
        self.mock_session_service.get_all_accounts.return_value = []
        self.mock_session_service.count_all_accounts.return_value = 25

        response = self.client.get("/admin/users?page=-1")
        assert response.status_code == 200
        assert b"Page 1 of 2" in response.data

    def test_list_all_users_as_non_admin_returns_403(self):
        fake_user = create_test_account(account_role=AccountRole.USER)
        self.mock_session_service.get_current_account.return_value = fake_user
        response = self.client.get("/admin/users")
        assert response.status_code == 403

    def test_non_admin_post_delete_another_returns_403(self):
        user = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.set_current_user(user)
        self.mock_session_service.get_current_account.return_value = user
        response = self.client.post("/account/delete", data={"account_id": 2})
        assert response.status_code == 403

    def test_admin_self_delete_returns_403(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        self.mock_session_service.get_current_account.return_value = admin
        self.mock_session_service.get_account_by_id.return_value = admin
        response = self.client.post("/account/delete")
        assert response.status_code == 403

    def test_self_delete_redirects(self):
        user = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.set_current_user(user)
        self.mock_session_service.get_current_account.return_value = user
        self.mock_session_service.get_account_by_id.return_value = user
        self.mock_session_service.delete_account.return_value = None
        response = self.client.post("/account/delete", follow_redirects=True)
        assert response.status_code == 200
        assert b"articles" in response.data or b"Account deleted" in response.data

    def test_admin_delete_another_user_redirects(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.set_current_user(admin)
        self.mock_session_service.get_current_account.return_value = admin
        self.mock_session_service.get_account_by_id.return_value = target
        self.mock_session_service.get_all_accounts.return_value = []
        self.mock_session_service.delete_account.return_value = None
        response = self.client.post("/account/delete", data={"account_id": 2}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Manage Users" in response.data or b"Account deleted" in response.data

    def test_admin_delete_nonexistent_target_redirects_with_flash(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        self.mock_session_service.get_current_account.return_value = admin
        self.mock_session_service.get_account_by_id.return_value = None
        self.mock_session_service.get_all_accounts.return_value = []
        response = self.client.post("/account/delete", data={"account_id": 999}, follow_redirects=True)
        assert response.status_code == 200
        assert b"not found" in response.data or b"Account not found" in response.data

    def test_update_email_success(self):
        fake_user = create_test_account(account_id=1, account_email="old@test.com")
        self.mock_session_service.get_current_account.return_value = fake_user
        self.mock_session_service.update_email.return_value = None
        response = self.client.post(
            "/profile/email",
            data={"email": "new@test.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Email updated." in response.data
        assert b"alert-success" in response.data
        self.mock_session_service.update_email.assert_called_once_with("new@test.com")

    def test_update_email_unauthenticated(self):
        self.mock_session_service.get_current_account.return_value = None
        response = self.client.post(
            "/profile/email",
            data={"email": "new@test.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Please sign in." in response.data
        self.mock_session_service.update_email.assert_not_called()

    def test_update_email_error(self):
        fake_user = create_test_account(account_id=1, account_email="old@test.com")
        self.mock_session_service.get_current_account.return_value = fake_user
        self.mock_session_service.update_email.return_value = "This email is already taken."
        response = self.client.post(
            "/profile/email",
            data={"email": "taken@test.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"This email is already taken." in response.data
        assert b"alert-error" in response.data
        self.mock_session_service.update_email.assert_called_once_with("taken@test.com")

    def test_update_password_success(self):
        fake_user = create_test_account(account_id=1)
        self.mock_session_service.get_current_account.return_value = fake_user
        self.mock_session_service.update_password.return_value = None
        response = self.client.post(
            "/profile/password",
            data={"new_password": "new_secret"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Password updated." in response.data
        assert b"alert-success" in response.data
        self.mock_session_service.update_password.assert_called_once_with("new_secret")

    def test_update_password_unauthenticated(self):
        self.mock_session_service.get_current_account.return_value = None
        response = self.client.post(
            "/profile/password",
            data={"new_password": "new_secret"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Please sign in." in response.data
        self.mock_session_service.update_password.assert_not_called()


class TestAccountSessionChangeRole(FlaskInputAdapterTestBase):
    """
    Tests for the change_role POST endpoint.
    """

    def setup_method(self):
        super().setup_method()
        self.mock_session_service = Mock(spec=AccountSessionManagementPort, autospec=True)
        self.mock_file_service = Mock(spec=FileManagementPort, autospec=True)
        self.adapter = AccountSessionAdapter(
            session_service=self.mock_session_service,
            file_service=self.mock_file_service,
        )
        self.app.add_url_rule(
            "/admin/users/<int:account_id>/role",
            view_func=self.adapter.change_role,
            methods=["POST"],
            endpoint="auth.change_role",
        )
        self.app.add_url_rule(
            "/users/<username>",
            view_func=lambda username: "profile",
            endpoint="auth.user_profile",
        )
        self.app.add_url_rule(
            "/admin/users",
            view_func=lambda: "users",
            endpoint="auth.list_all_users",
        )

    def test_admin_change_role_redirects(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_username="targetuser")
        self.set_current_user(admin)
        self.mock_session_service.get_current_account.return_value = admin
        self.mock_session_service.update_account_role.return_value = None
        self.mock_session_service.get_account_by_id.return_value = target
        response = self.client.post(
            "/admin/users/2/role",
            data={"role": "author"},
        )
        assert response.status_code == 302
        assert response.location.endswith("/users/targetuser")
        self.mock_session_service.update_account_role.assert_called_once_with(
            admin_id=1, target_id=2, new_role="author",
        )

    def test_admin_change_role_nonexistent_target(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        self.mock_session_service.get_current_account.return_value = admin
        self.mock_session_service.update_account_role.return_value = "Account not found."
        self.mock_session_service.get_account_by_id.return_value = None
        response = self.client.post(
            "/admin/users/999/role",
            data={"role": "author"},
        )
        assert response.status_code == 302

    def test_non_admin_change_role_returns_403(self):
        user = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.set_current_user(user)
        self.mock_session_service.get_current_account.return_value = user
        response = self.client.post(
            "/admin/users/2/role",
            data={"role": "author"},
        )
        assert response.status_code == 403


class TestAccountSessionBeforeRequestHook(FlaskInputAdapterTestBase):
    """
    Tests for the 'before_request' lifecycle hook registered by AccountSessionAdapter.
    Verifies that the current user identity is correctly injected into flask.g
    before every request, for both authenticated and anonymous scenarios.
    """

    def setup_method(self):
        super().setup_method()
        self.mock_session_service = Mock(spec=AccountSessionManagementPort, autospec=True)
        self.mock_file_service = Mock(spec=FileManagementPort, autospec=True)
        self.adapter = AccountSessionAdapter(
            session_service=self.mock_session_service,
            file_service=self.mock_file_service,
        )

    def _capture_handler(self, **kwargs):
        """Route handler that captures the current_user from flask.g."""
        self._captured_user = global_request_context.get("current_user")
        return "OK", 200

    def _capture_user_via_route(self, endpoint):
        """Triggers a request on a dummy route to capture the injected user."""
        self.app.add_url_rule(f"/{endpoint}", view_func=self._capture_handler, endpoint=endpoint)
        self.client.get(f"/{endpoint}")
        return self._captured_user

    def test_before_request_injects_authenticated_user(self):
        test_account = create_test_account(account_username="AgentSmith", account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = test_account
        self.adapter.register_before_request_handler(self.app)
        captured_user = self._capture_user_via_route("test-authenticated")
        assert captured_user is not None
        assert isinstance(captured_user, Account)
        assert captured_user.account_username == "AgentSmith"
        assert captured_user.account_role == AccountRole.ADMIN

    def test_before_request_injects_author_user(self):
        test_account = create_test_account(account_username="AuthorWriter", account_role=AccountRole.AUTHOR)
        self.mock_session_service.get_current_account.return_value = test_account
        self.adapter.register_before_request_handler(self.app)
        captured_user = self._capture_user_via_route("test-author")
        assert captured_user is not None
        assert captured_user.account_role == AccountRole.AUTHOR

    def test_before_request_injects_none_when_anonymous(self):
        self.mock_session_service.get_current_account.return_value = None
        self.adapter.register_before_request_handler(self.app)
        captured_user = self._capture_user_via_route("test-anonymous")
        assert captured_user is None

    def test_before_request_isolation_between_requests(self):
        self.app.add_url_rule("/req1", view_func=self._capture_handler, endpoint="req1")
        self.app.add_url_rule("/req2", view_func=self._capture_handler, endpoint="req2")
        self._register_dummy_route("/register", "registration.register", "registration")
        self._register_dummy_route("/login", "auth.login", "login")
        self._register_dummy_route("/articles", "article.list_articles", "articles")
        admin_account = create_test_account(account_username="Admin", account_role=AccountRole.ADMIN)
        self.mock_session_service.get_current_account.return_value = admin_account
        self.adapter.register_before_request_handler(self.app)
        self.client.get("/req1")
        user1 = self._captured_user
        assert user1 is not None and user1.account_username == "Admin"
        self.mock_session_service.get_current_account.return_value = None
        self.client.get("/req2")
        user2 = self._captured_user
        assert user2 is None
