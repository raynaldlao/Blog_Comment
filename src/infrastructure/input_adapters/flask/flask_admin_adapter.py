import math

from flask import abort, flash, redirect, render_template, request, url_for
from flask import g as global_request_context
from flask_babel import gettext as _
from werkzeug.wrappers.response import Response

from blog_exceptions import BlogCommentError
from flask_setup.auth_helpers import require_auth
from src.application.domain.account import AccountRole
from src.application.input_ports.admin_management import AdminManagementPort
from src.infrastructure.input_adapters.dto.account_response import AccountResponse


class AdminAdapter:
    """Flask input adapter for admin-only account management.

    All view methods are protected by @require_auth() decorator
    which rejects unauthenticated requests. Each method additionally
    checks admin role and aborts with 403 for non-admin users.
    """

    def __init__(self, admin_service: AdminManagementPort):
        """Initialize adapter with admin management service.

        Args:
            admin_service: Input port for admin account operations.
        """
        self.admin_service = admin_service

    def _require_admin_role(self) -> None:
        current_account = global_request_context.get("current_user")
        if current_account.account_role != AccountRole.ADMIN:
            abort(403)

    @require_auth()
    def list_all_users(self) -> str | Response:
        """Render admin user list with pagination and search.

        Returns:
            Rendered user_list.html template.

        Raises:
            403: If current user is not authenticated or not admin.
        """
        self._require_admin_role()

        query = request.args.get("q", "").strip()
        page = max(1, request.args.get("page", 1, type=int))
        per_page = 20

        if query:
            accounts = self.admin_service.search_accounts(query, page=page, per_page=per_page)
            total = self.admin_service.count_search_accounts(query)
        else:
            accounts = self.admin_service.get_all_accounts(page=page, per_page=per_page)
            total = self.admin_service.count_all_accounts()

        total_pages = max(1, math.ceil(total / per_page))
        users_dto = [AccountResponse.from_domain(acc) for acc in accounts]

        return render_template(
            "user_list.html",
            users=users_dto,
            page=page,
            total_pages=total_pages,
            has_prev=(page > 1),
            has_next=(page < total_pages),
            query=query,
            total_count=total,
        )

    @require_auth()
    def delete_account(self, account_id: int) -> Response:
        """Handle admin deletion of another user account.

        Admin self-delete is forbidden (403).

        Returns:
            Redirect response.

        Raises:
            403: If admin tries to self-delete, or target is another admin.
        """
        self._require_admin_role()

        if account_id == global_request_context.get("current_user").account_id:
            abort(403)

        target = self.admin_service.get_account_by_id(account_id)
        if not target:
            flash(_("Account not found."), "error")
            return redirect(url_for("admin.list_all_users"))

        if target.account_role == AccountRole.ADMIN:
            abort(403)

        self.admin_service.delete_account(account_id)
        flash(_("Account deleted."), "success")
        return redirect(url_for("admin.list_all_users"))

    @require_auth()
    def change_role(self, account_id: int) -> Response:
        """Handle role change form submission.

        Args:
            account_id: ID of account whose role to update.

        Returns:
            Redirect to target profile or user list.

        Raises:
            403: If current user is not admin.
        """
        self._require_admin_role()

        current_account = global_request_context.get("current_user")
        new_role = request.form.get("role", "")
        try:
            self.admin_service.update_account_role(
                admin_id=current_account.account_id,
                target_id=account_id,
                new_role=new_role,
            )
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Role updated."), "success")

        target = self.admin_service.get_account_by_id(account_id)
        if target:
            return redirect(url_for("auth.user_profile", username=target.account_username))
        return redirect(url_for("admin.list_all_users"))

    @require_auth()
    def ban_account(self, account_id: int) -> Response:
        """Handle ban form submission.

        Args:
            account_id: ID of account to ban.

        Returns:
            Redirect to user list.

        Raises:
            403: If current user is not admin.
        """
        self._require_admin_role()

        current_account = global_request_context.get("current_user")
        ban_reason = request.form.get("ban_reason", "").strip() or None
        try:
            self.admin_service.ban_account(
                admin_id=current_account.account_id,
                target_account_id=account_id,
                ban_reason=ban_reason,
            )
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Account banned."), "success")

        return redirect(url_for("admin.list_all_users"))

    @require_auth()
    def unban_account(self, account_id: int) -> Response:
        """Handle unban form submission.

        Args:
            account_id: ID of account to unban.

        Returns:
            Redirect to user list.

        Raises:
            403: If current user is not admin.
        """
        self._require_admin_role()

        current_account = global_request_context.get("current_user")
        try:
            self.admin_service.unban_account(
                admin_id=current_account.account_id,
                target_account_id=account_id,
            )
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Account unbanned."), "success")

        return redirect(url_for("admin.list_all_users"))
