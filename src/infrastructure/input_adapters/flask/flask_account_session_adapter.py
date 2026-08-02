from flask import abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask import g as global_request_context
from flask_babel import gettext as _
from pydantic import ValidationError

from blog_exceptions import BlogCommentError
from src.application.input_ports.account_session_management import AccountSessionManagementPort
from src.infrastructure.input_adapters.dto.account_response import AccountResponse
from src.infrastructure.input_adapters.dto.update_password_request import UpdatePasswordRequest


class AccountSessionAdapter:
    """
    Flask Input Adapter for account session, profile, and identity operations.

    Implements a single input port: AccountSessionManagementPort.
    Orchestrates cross-cutting operations (avatar upload, account deletion)
    by delegating to the session service, which internally coordinates
    file and comment services.
    """

    def __init__(self, session_service: AccountSessionManagementPort):
        """
        Initializes the AccountSessionAdapter with the required session service.

        Args:
            session_service (AccountSessionManagementPort): The input port for session management.
        """
        self.session_service = session_service

    def _identify_user(self):
        """Injects the current user into the global request context.

        Checks for a pre-existing session (user_id + session_token in cookie).
        After fetching the account, compares the cookie token against the
        database token. On mismatch (session stolen / another login elsewhere):
        - Flashes a disconnection message in the "error" category.
        - Returns a redirect to the article list (non-API paths only).
        - API paths (/api/) skip the redirect; the 401 is handled by the
          React front-end via FlaskSessionAdapter returning None.
        If no mismatch or no pre-existing session, proceeds normally.

        Static file paths (/static/) skip the DB lookup entirely to
        avoid unnecessary connection pool pressure on every page asset
        (JS, CSS, images, fonts).
        """
        if request.path.startswith("/static/"):
            global_request_context.current_user = None
            return None

        had_session = (
            session.get("user_id") is not None
            and session.get("session_token") is not None
        )
        global_request_context.current_user = self.session_service.get_current_account()
        if had_session and global_request_context.current_user is None:
            flash(
                _("You have been disconnected because your account was logged in from another location."),
                "error",
            )
            if not request.path.startswith("/api/"):
                return redirect(url_for("article.list_articles"))

    def register_before_request_handler(self, app):
        """
        Registers a global 'before_request' hook on the Flask application.

        FUNCTIONING:
        - Registration: This method is called ONCE during the app bootstrap.
        - Execution: The internal '_identify_user' hook is called by Flask
          AUTOMATICALLY before EVERY SINGLE request.
        - Persistence: It populates the 'global_request_context' (flask.g)
          with the domain Account entity, making identity available
          to all downstream adapters and templates.

        Args:
            app (Flask): The Flask application instance.
        """
        app.before_request(self._identify_user)

    def logout(self):
        """
        Terminates the current user session and redirects to the articles list.

        Returns:
            Response: A Flask redirect response.

        Raises:
            403: If no user is currently authenticated.
        """
        if not self.session_service.get_current_account():
            abort(403)
        self.session_service.terminate_session()
        flash(_("You have been logged out."), "info")
        return redirect(url_for("article.list_articles"))

    def set_lang(self, locale: str):
        """
        Flask view that sets the user's language preference in the session.

        Accepts 'fr' or 'en'. Invalid values are silently ignored.
        Redirects to the previous page (via Referer header) or the article
        list as fallback.

        Args:
            locale (str): The target locale, extracted from the URL path.

        Returns:
            Response: A redirect response.
        """
        if locale in ("fr", "en"):
            session["lang"] = locale
        return redirect(request.referrer or url_for("article.list_articles"))

    def display_profile(self):
        """
        Renders the current user's profile if an active session is found.
        Redirects to the login page otherwise.

        Returns:
            str | Response: The rendered profile HTML or a redirect response.
        """
        account = self.session_service.get_current_account()

        if not account:
            flash(_("Please sign in to view your profile."), "error")
            return redirect(url_for("auth.login"))

        user_dto = AccountResponse.from_domain(account)
        return render_template("profile.html", user=user_dto, is_own_profile=True)

    def display_user_profile(self, username: str):
        """
        Renders a public user profile page for the given username.

        Accessible to all users (authenticated or anonymous).
        Sensitive fields (email, member since) are shown only to
        the profile owner or an admin viewer.

        Args:
            username: The username of the profile to display.

        Returns:
            str: The rendered profile HTML.

        Raises:
            404: If no account exists with the given username.
        """
        account = self.session_service.get_account_by_username(username)

        if not account:
            abort(404)

        user_dto = AccountResponse.from_domain(account)

        current_account = getattr(global_request_context, "current_user", None)

        return render_template(
            "profile.html",
            user=user_dto,
            is_own_profile=bool(
                current_account and current_account.account_id == account.account_id
            ),
        )

    def upload_profile_photo(self):
        """
        Handles profile photo upload via multipart POST.

        Validates authentication, delegates file storage and avatar update
        to the session service, which internally coordinates the file service.

        Returns:
            Response: JSON with avatar_url on success (200),
                      or error message (400/401).
        """
        current_account = getattr(global_request_context, "current_user", None)
        if not current_account:
            return jsonify({"error": _("Authentication required.")}), 401

        uploaded_file = request.files.get("file")
        if not uploaded_file or not uploaded_file.filename:
            return jsonify({"error": _("No file provided.")}), 400

        file_id = self.session_service.update_profile_photo(
            file_data=uploaded_file.read(),
            filename=uploaded_file.filename,
            mime_type=uploaded_file.content_type or "application/octet-stream",
        )
        if not file_id:
            return jsonify({"error": _("Failed to upload profile photo.")}), 400

        return jsonify({
            "avatar_url": url_for("file.serve_file", file_id=file_id, filename="avatar"),
        }), 200

    def remove_profile_photo(self):
        """
        Removes the current user's profile photo.

        Delegates file deletion and avatar ref update to the session service.
        Redirects back to profile with a flash message on success or error.

        Returns:
            Response: A Flask redirect response.
        """
        account = self.session_service.get_current_account()
        if not account:
            flash(_("Please sign in."), "error")
            return redirect(url_for("auth.login"))

        removed = self.session_service.remove_profile_photo()
        if not removed:
            flash(_("No avatar to remove."), "error")
            return redirect(url_for("auth.profile"))

        flash(_("Profile photo removed."), "success")
        return redirect(url_for("auth.profile"))

    def update_email(self):
        """
        Handles email address change form submission.

        Validates authentication, extracts the new email from the form data,
        and delegates the update to the session service. Redirects back to
        the profile page with a flash message on success or error.

        Returns:
            Response: A Flask redirect response to the profile page.
        """
        account = self.session_service.get_current_account()
        if not account:
            flash(_("Please sign in."), "error")
            return redirect(url_for("auth.login"))

        new_email = request.form.get("email", "").strip()
        if not new_email:
            flash(_("Email is required."), "error")
            return redirect(url_for("auth.profile"))

        try:
            self.session_service.update_email(new_email)
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Email updated."), "success")
        return redirect(url_for("auth.profile"))

    def update_password(self):
        """
        Handles password change form submission.

        Validates the new password via the UpdatePasswordRequest DTO,
        then hashes and persists via the session service.
        Redirects back to the profile page on success or error.

        Returns:
            Response: A Flask redirect response to the profile page.
        """
        account = self.session_service.get_current_account()
        if not account:
            flash(_("Please sign in."), "error")
            return redirect(url_for("auth.login"))

        try:
            dto = UpdatePasswordRequest(
                password=request.form.get("new_password", "")
            )
        # Pydantic library exception — caught at web boundary for flash + redirect.
        # Not in blog_exceptions.py. Do not move it there.
        except ValidationError as e:
            for error in e.errors():
                msg = error["msg"].removeprefix("Value error, ")
                flash(_(msg), "error")
            return redirect(url_for("auth.profile"))

        try:
            self.session_service.update_password(dto.password)
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Password updated."), "success")
        return redirect(url_for("auth.profile"))

    def delete_account(self):
        account = self.session_service.get_current_account()
        if not account:
            flash(_("Please sign in."), "error")
            return redirect(url_for("auth.login"))
        self.session_service.delete_own_account()
        flash(_("Account deleted."), "info")
        return redirect(url_for("article.list_articles"))


