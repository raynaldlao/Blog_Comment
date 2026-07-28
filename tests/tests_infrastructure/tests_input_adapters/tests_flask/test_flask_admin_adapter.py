from unittest.mock import Mock

from src.application.domain.account import AccountRole
from src.application.input_ports.admin_management import AdminManagementPort
from src.infrastructure.input_adapters.flask.flask_admin_adapter import AdminAdapter
from tests.test_domain_factories import create_test_account
from tests.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class TestAdminListAllUsers(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_admin_service = Mock(spec=AdminManagementPort, autospec=True)
        self.mock_admin_service.count_all_accounts.return_value = 0
        self.mock_admin_service.search_accounts.return_value = []
        self.mock_admin_service.count_search_accounts.return_value = 0

        self.adapter = AdminAdapter(
            admin_service=self.mock_admin_service,
        )

        self.app.add_url_rule(
            "/admin/users",
            view_func=self.adapter.list_all_users,
            methods=["GET"],
            endpoint="admin.list_all_users",
        )

        self.app.add_url_rule(
            "/admin/users/<int:account_id>/delete",
            view_func=self.adapter.delete_account,
            methods=["POST"],
            endpoint="admin.delete_account",
        )

        self.app.add_url_rule(
            "/admin/users/<int:account_id>/role",
            view_func=self.adapter.change_role,
            methods=["POST"],
            endpoint="admin.change_role",
        )

        self.app.add_url_rule(
            "/admin/users/<int:account_id>/ban",
            view_func=self.adapter.ban_account,
            methods=["POST"],
            endpoint="admin.ban_account",
        )

        self.app.add_url_rule(
            "/admin/users/<int:account_id>/unban",
            view_func=self.adapter.unban_account,
            methods=["POST"],
            endpoint="admin.unban_account",
        )

        self._register_dummy_route("/articles", "article.list_articles", "articles")
        self._register_dummy_route("/login", "auth.login", "login")
        self._register_dummy_route("/register", "registration.register", "register")
        self._register_dummy_route("/articles/new", "article.render_create_page", "new_article")
        self._register_dummy_route("/account/delete", "auth.delete_account", "delete_account")
        self._register_dummy_route("/profile", "auth.profile", "profile")
        self._register_dummy_route("/logout", "auth.logout", "logout")
        self._register_dummy_route("/lang/<locale>", "auth.set_lang", "set_lang")
        self._register_dummy_route("/users/<username>", "auth.user_profile", "user_profile")

    def test_list_all_users_as_admin(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.set_current_user(fake_admin)

        fake_users = [
            create_test_account(account_id=i, account_username=f"user{i}")
            for i in range(1, 26)
        ]

        self.mock_admin_service.get_all_accounts.return_value = fake_users[:20]
        self.mock_admin_service.count_all_accounts.return_value = 25

        response = self.client.get("/admin/users")
        assert response.status_code == 200
        assert b"user1" in response.data
        assert b"user20" in response.data
        assert b"page-link-num" in response.data
        assert b"jump-modal" in response.data

    def test_list_all_users_page_2(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.set_current_user(fake_admin)

        fake_users_page2 = [
            create_test_account(account_id=i, account_username=f"user{i}")
            for i in range(21, 26)
        ]

        self.mock_admin_service.get_all_accounts.return_value = fake_users_page2
        self.mock_admin_service.count_all_accounts.return_value = 25

        response = self.client.get("/admin/users?page=2")
        assert response.status_code == 200
        assert b"user21" in response.data
        assert b"user25" in response.data
        assert b"page-link-num" in response.data
        assert b"jump-modal" in response.data

    def test_list_all_users_with_search(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.set_current_user(fake_admin)

        fake_results = [
            create_test_account(account_id=i, account_username=f"user{i}")
            for i in range(1, 26)
        ]

        self.mock_admin_service.search_accounts.return_value = fake_results[:20]
        self.mock_admin_service.count_search_accounts.return_value = 25

        response = self.client.get("/admin/users?q=user")
        assert response.status_code == 200
        assert b"user1" in response.data
        assert b"user20" in response.data
        assert b"page-link-num" in response.data
        assert b"jump-modal" in response.data
        self.mock_admin_service.search_accounts.assert_called_once_with("user", page=1, per_page=20)
        self.mock_admin_service.count_search_accounts.assert_called_once_with("user")

    def test_list_all_users_search_no_results(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.set_current_user(fake_admin)
        response = self.client.get("/admin/users?q=zzz")
        assert response.status_code == 200
        assert b"Manage Users (0 users)" in response.data
        self.mock_admin_service.search_accounts.assert_called_once_with("zzz", page=1, per_page=20)
        self.mock_admin_service.count_search_accounts.assert_called_once_with("zzz")

    def test_list_all_users_page_invalid(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.set_current_user(fake_admin)
        self.mock_admin_service.get_all_accounts.return_value = []
        self.mock_admin_service.count_all_accounts.return_value = 25
        response = self.client.get("/admin/users?page=-1")
        assert response.status_code == 200
        assert b"page-link-num" in response.data

    def test_list_all_users_shows_total_count(self):
        fake_admin = create_test_account(account_role=AccountRole.ADMIN)
        self.set_current_user(fake_admin)

        self.mock_admin_service.get_all_accounts.return_value = [
            create_test_account(account_id=i) for i in range(1, 21)
        ]

        self.mock_admin_service.count_all_accounts.return_value = 47
        response = self.client.get("/admin/users")
        assert response.status_code == 200
        assert b"Manage Users (47 users)" in response.data

    def test_list_all_users_as_non_admin_returns_403(self):
        fake_user = create_test_account(account_role=AccountRole.USER)
        self.set_current_user(fake_user)
        response = self.client.get("/admin/users")
        assert response.status_code == 403

    def test_non_admin_post_delete_another_returns_403(self):
        user = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.set_current_user(user)
        response = self.client.post("/admin/users/2/delete")
        assert response.status_code == 403

    def test_admin_self_delete_returns_403(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        response = self.client.post("/admin/users/1/delete")
        assert response.status_code == 403

    def test_admin_delete_another_user_redirects(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.USER)
        self.set_current_user(admin)
        self.mock_admin_service.get_account_by_id.return_value = target
        self.mock_admin_service.get_all_accounts.return_value = []
        self.mock_admin_service.delete_account.return_value = None
        response = self.client.post("/admin/users/2/delete", follow_redirects=True)
        assert response.status_code == 200
        assert b"Manage Users (0 users)" in response.data or b"Account deleted" in response.data
        self.mock_admin_service.delete_account.assert_called_once_with(2)

    def test_admin_delete_nonexistent_target_redirects_with_flash(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        self.mock_admin_service.get_account_by_id.return_value = None
        self.mock_admin_service.get_all_accounts.return_value = []
        response = self.client.post("/admin/users/999/delete", follow_redirects=True)
        assert response.status_code == 200
        assert b"not found" in response.data or b"Account not found" in response.data
        self.mock_admin_service.delete_account.assert_not_called()

    def test_admin_delete_another_admin_returns_403(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        self.mock_admin_service.get_account_by_id.return_value = target
        response = self.client.post("/admin/users/2/delete")
        assert response.status_code == 403
        self.mock_admin_service.delete_account.assert_not_called()


class TestAdminChangeRole(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_admin_service = Mock(spec=AdminManagementPort, autospec=True)
        self.adapter = AdminAdapter(
            admin_service=self.mock_admin_service,
        )

        self.app.add_url_rule(
            "/admin/users/<int:account_id>/role",
            view_func=self.adapter.change_role,
            methods=["POST"],
            endpoint="admin.change_role",
        )

        self.app.add_url_rule(
            "/users/<username>",
            view_func=lambda username: "profile",
            endpoint="auth.user_profile",
        )

        self.app.add_url_rule(
            "/admin/users",
            view_func=lambda: "users",
            endpoint="admin.list_all_users",
        )

    def test_admin_change_role_redirects(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        target = create_test_account(account_id=2, account_username="targetuser")
        self.set_current_user(admin)

        self.mock_admin_service.update_account_role.return_value = None
        self.mock_admin_service.get_account_by_id.return_value = target
        response = self.client.post(
            "/admin/users/2/role",
            data={"role": "author"},
        )

        assert response.status_code == 302
        assert response.location.endswith("/users/targetuser")
        self.mock_admin_service.update_account_role.assert_called_once_with(
            admin_id=1, target_id=2, new_role="author",
        )

    def test_admin_change_role_nonexistent_target(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)

        from blog_exceptions import AccountNotFoundError
        self.mock_admin_service.update_account_role.side_effect = AccountNotFoundError("Account not found.")
        self.mock_admin_service.get_account_by_id.return_value = None
        response = self.client.post(
            "/admin/users/999/role",
            data={"role": "author"},
        )

        assert response.status_code == 302

    def test_non_admin_change_role_returns_403(self):
        user = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.set_current_user(user)

        response = self.client.post(
            "/admin/users/2/role",
            data={"role": "author"},
        )

        assert response.status_code == 403


class TestAdminBan(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_admin_service = Mock(spec=AdminManagementPort, autospec=True)
        self.adapter = AdminAdapter(
            admin_service=self.mock_admin_service,
        )

        self.app.add_url_rule(
            "/admin/users/<int:account_id>/ban",
            view_func=self.adapter.ban_account,
            methods=["POST"],
            endpoint="admin.ban_account",
        )

        self.app.add_url_rule(
            "/admin/users/<int:account_id>/unban",
            view_func=self.adapter.unban_account,
            methods=["POST"],
            endpoint="admin.unban_account",
        )

        self._register_dummy_route("/admin/users", "admin.list_all_users", "users")

    def test_admin_ban_user_redirects(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        self.mock_admin_service.ban_account.return_value = None
        response = self.client.post("/admin/users/2/ban", data={"ban_reason": "Spam"})
        assert response.status_code == 302

        self.mock_admin_service.ban_account.assert_called_once_with(
            admin_id=1, target_account_id=2, ban_reason="Spam",
        )

    def test_admin_unban_user_redirects(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        self.mock_admin_service.unban_account.return_value = None
        response = self.client.post("/admin/users/2/unban")
        assert response.status_code == 302

        self.mock_admin_service.unban_account.assert_called_once_with(
            admin_id=1, target_account_id=2,
        )

    def test_admin_unban_error_flashes_message(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        from blog_exceptions import AccountNotFoundError
        self.mock_admin_service.unban_account.side_effect = AccountNotFoundError("Account not found.")
        response = self.client.post("/admin/users/2/unban", follow_redirects=True)
        assert response.status_code == 200
        assert b"Account not found" in response.data
        self.mock_admin_service.unban_account.assert_called_once()

    def test_non_admin_ban_returns_403(self):
        user = create_test_account(account_id=1, account_role=AccountRole.USER)
        self.set_current_user(user)
        response = self.client.post("/admin/users/2/ban", data={"ban_reason": "Spam"})
        assert response.status_code == 403
        self.mock_admin_service.ban_account.assert_not_called()

    def test_admin_ban_another_admin_returns_302_with_flash(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        from blog_exceptions import AuthorizationError
        self.mock_admin_service.ban_account.side_effect = AuthorizationError("Cannot ban another admin.")
        response = self.client.post("/admin/users/2/ban", data={"ban_reason": "Spam"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Cannot ban another admin" in response.data
        self.mock_admin_service.ban_account.assert_called_once()

    def test_admin_ban_nonexistent_user_redirects_with_flash(self):
        admin = create_test_account(account_id=1, account_role=AccountRole.ADMIN)
        self.set_current_user(admin)
        from blog_exceptions import AccountNotFoundError
        self.mock_admin_service.ban_account.side_effect = AccountNotFoundError("Account not found.")
        response = self.client.post("/admin/users/999/ban", data={"ban_reason": "Spam"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Account not found" in response.data
        self.mock_admin_service.ban_account.assert_called_once()
