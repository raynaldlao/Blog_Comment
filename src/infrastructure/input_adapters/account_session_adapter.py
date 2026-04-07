from flask import flash, redirect, render_template, url_for
from flask.views import MethodView

from src.application.input_ports.account_session_management import AccountSessionManagement
from src.infrastructure.input_adapters.dto.account_response import AccountResponse


class AccountSessionAdapter(MethodView):
    """
    Unified adapter for session-related operations (Logout and Profile).
    It bridges HTTP requests to the AccountSessionManagement port.

    This class adheres to Rule #6 (Adapter Uniqueness) by centralizing
    all session-related Web actions into a single infrastructure component.
    """

    def __init__(self, session_service: AccountSessionManagement):
        """
        Initializes the AccountSessionAdapter with the required session service.

        Args:
            session_service (AccountSessionManagement): The domain service for session management.
        """
        self.session_service = session_service

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
