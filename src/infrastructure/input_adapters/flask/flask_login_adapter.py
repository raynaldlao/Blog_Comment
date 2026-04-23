from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView
from pydantic import ValidationError

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
        return render_template("login.html")

    def authenticate(self):
        """
        Processes the login form submission.
        Validates the input using LoginRequest DTO and calls the authentication service.

        Returns:
            Response: Redirects to the articles list on success, or back to login on failure.
        """
        try:
            login_data = LoginRequest(
                username=request.form.get("username", ""),
                password=request.form.get("password", "")
            )
        except ValidationError as e:
            for error in e.errors():
                location = str(error["loc"][0]) if error["loc"] else "Request"
                flash(f"Validation Error ({location}): {error['msg']}")
            return redirect(url_for("auth.login"))

        account = self.login_service.authenticate_user(
            username=login_data.username,
            password=login_data.password
        )

        if account:
            return redirect(url_for("article.list_articles"))

        flash("Invalid username or password.")
        return redirect(url_for("auth.login"))
