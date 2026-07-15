from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask import g as global_request_context
from flask.views import MethodView
from src.application.application_exceptions import FileTooLargeError, FileTypeError
from src.application.domain.account import AccountRole
from src.application.input_ports.account_session_management import AccountSessionManagementPort
from src.application.input_ports.file_management import FileManagementPort
from src.infrastructure.input_adapters.dto.account_response import AccountResponse


class AccountSessionAdapter(MethodView):
    """
    Flask Input Adapter for Account Session, Profile,
    and global request identity resolution.

    Centralizes ALL session-related Web actions into a single infrastructure
    component, adhering to Rule #6 (Adapter Uniqueness). This includes:
    - User identity injection via a 'before_request' hook.
    - User logout (session clearing).
    - User profile display.
    """

    def __init__(
        self,
        session_service: AccountSessionManagementPort,
        file_service: FileManagementPort,
    ):
        """
        Initializes the AccountSessionAdapter with the required session service.

        Args:
            session_service (AccountSessionManagementPort): The input port for session management.
            file_service (FileManagementPort): The input port for file management.
        """
        self.session_service = session_service
        self.file_service = file_service

    def _identify_user(self):
        """Injects the current user into the global request context."""
        global_request_context.current_user = self.session_service.get_current_account()

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
        """
        self.session_service.terminate_session()
        flash("You have been logged out.", "info")
        return redirect(url_for("article.list_articles"))

    def display_profile(self):
        """
        Renders the current user's profile if an active session is found.
        Redirects to the login page otherwise.

        Returns:
            str | Response: The rendered profile HTML or a redirect response.
        """
        account = self.session_service.get_current_account()

        if not account:
            flash("Please sign in to view your profile.", "error")
            return redirect(url_for("auth.login"))

        user_dto = AccountResponse.from_domain(account)
        return render_template("profile.html", user=user_dto, current_user=user_dto, is_own_profile=True)

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

        current_user_dto = None
        current_account = getattr(global_request_context, "current_user", None)
        if current_account:
            current_user_dto = AccountResponse.from_domain(current_account)

        return render_template(
            "profile.html",
            user=user_dto,
            current_user=current_user_dto,
            is_own_profile=bool(
                current_account and current_account.account_id == account.account_id
            ),
        )

    def upload_profile_photo(self):
        """
        Handles profile photo upload via multipart POST.

        Validates authentication, delegates file upload to the file service,
        and persists the avatar reference on the current account.

        Returns:
            Response: JSON with avatar_url on success (200),
                      or error message (400/401).
        """
        current_account = getattr(global_request_context, "current_user", None)
        if not current_account:
            return jsonify({"error": "Authentication required."}), 401

        uploaded_file = request.files.get("file")
        if not uploaded_file or not uploaded_file.filename:
            return jsonify({"error": "No file provided."}), 400

        file_data = uploaded_file.read()
        try:
            file_record = self.file_service.upload_file(
                filename=uploaded_file.filename,
                data=file_data,
                mime_type=uploaded_file.content_type or "application/octet-stream",
            )
        except (FileTooLargeError, FileTypeError) as e:
            return jsonify({"error": str(e)}), 400

        self.session_service.update_avatar(file_record.file_id)

        return jsonify({
            "avatar_url": url_for("file.serve_file", file_id=file_record.file_id, filename="avatar"),
        }), 200

    def remove_profile_photo(self):
        """
        Removes the current user's profile photo.

        Deletes the uploaded file from storage via the file service,
        then clears the avatar_file_id reference on the account.

        Redirects back to profile with a flash message on success or error.

        Returns:
            Response: A Flask redirect response.
        """
        account = self.session_service.get_current_account()
        if not account:
            flash("Please sign in.", "error")
            return redirect(url_for("auth.login"))

        avatar_file_id = account.avatar_file_id
        if not avatar_file_id:
            flash("No avatar to remove.", "error")
            return redirect(url_for("auth.profile"))

        try:
            self.file_service.delete_file(avatar_file_id)
            self.session_service.update_avatar(None)
        except Exception:
            flash("Failed to remove profile photo.", "error")
            return redirect(url_for("auth.profile"))

        flash("Profile photo removed.", "success")
        return redirect(url_for("auth.profile"))

    def list_all_users(self):
        """
        Renders the admin-only user list page.

        Access restricted to admin role. Non-admin users receive a 403.
        Displays all registered users with username, email, role, and join date.

        Returns:
            str: The rendered user_list.html template.

        Raises:
            403: If the current user is not authenticated or not an admin.
        """
        current_account = self.session_service.get_current_account()
        if not current_account or current_account.account_role != AccountRole.ADMIN:
            abort(403)

        accounts = self.session_service.get_all_accounts()
        users_dto = [AccountResponse.from_domain(acc) for acc in accounts]

        return render_template(
            "user_list.html",
            users=users_dto,
            current_user=current_account,
        )
