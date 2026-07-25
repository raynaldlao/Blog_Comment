from flask import flash, redirect, render_template, request, url_for
from flask import g as global_request_context
from flask.views import MethodView
from flask_babel import gettext as _
from pydantic import ValidationError

from blog_exceptions import AccountBannedError, AuthenticationError
from src.application.input_ports.login_management import LoginManagementPort
from src.infrastructure.input_adapters.dto.login_request import LoginRequest


class LoginAdapter(MethodView):
    """
    Flask Input Adapter for Authentication operations.
    Translates web requests into domain operations and renders HTML templates.
    """

    def __init__(self, login_service: LoginManagementPort):
        """
        Initializes the LoginAdapter with the required login service.

        Args:
            login_service (LoginManagementPort): The domain service for authentication.
        """
        self.login_service = login_service

    def render_login_page(self):
        """
        Renders the login page to the user.

        Returns:
            str: The rendered HTML for the login page.
        """
        user = global_request_context.get("current_user")
        return render_template("login.html", current_user=user)

    def authenticate(self):
        """
        Processes the login form submission.
        Validates the input using LoginRequest DTO and calls the authentication service.

        Returns:
            Response: Redirects to the articles list on success, or back to login on failure.
        """
        user = global_request_context.get("current_user")
        submitted_username = request.form.get("username", "")

        try:
            login_data = LoginRequest(
                username=submitted_username,
                password=request.form.get("password", "")
            )
        # Pydantic library exception — caught at web boundary for flash + redirect.
        # Not in blog_exceptions.py. Do not move it there.
        except ValidationError as e:
            for error in e.errors():
                location = str(error["loc"][0]) if error["loc"] else "Request"
                flash(_("Validation Error (%(location)s): %(message)s", location=location, message=error["msg"]), "error")
            return render_template("login.html", current_user=user, username=submitted_username)

        try:
            self.login_service.authenticate_user(
                username=login_data.username,
                password=login_data.password
            )
        except AccountBannedError:
            flash(_("This account has been banned."), "error")
        except AuthenticationError:
            flash(_("Invalid username or password."), "error")
        else:
            return redirect(url_for("article.list_articles"))

        return render_template("login.html", current_user=user, username=login_data.username)
