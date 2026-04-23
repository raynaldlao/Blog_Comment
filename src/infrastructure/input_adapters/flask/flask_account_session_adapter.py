from flask import flash, redirect, render_template, url_for
from flask import g as global_request_context
from flask.views import MethodView

from src.application.input_ports.account_session_management import AccountSessionManagementPort
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

    def __init__(self, session_service: AccountSessionManagementPort):
        """
        Initializes the AccountSessionAdapter with the required session service.

        Args:
            session_service (AccountSessionManagementPort): The input port for session management.
        """
        self.session_service = session_service

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
        flash("You have been logged out.")
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
            flash("Please sign in to view your profile.")
            return redirect(url_for("auth.login"))

        user_dto = AccountResponse.from_domain(account)
        return render_template("profile.html", user=user_dto)
