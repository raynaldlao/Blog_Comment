from flask import flash, redirect, render_template, request, url_for
from flask_babel import gettext as _
from pydantic import ValidationError

from blog_exceptions import BlogCommentError
from src.application.input_ports.registration_management import RegistrationManagementPort
from src.infrastructure.input_adapters.dto.registration_request import RegistrationRequest


class RegistrationAdapter:
    """
    Flask Input Adapter for Registration operations.
    Translates web requests into domain operations and renders HTML templates.
    """

    def __init__(self, registration_service: RegistrationManagementPort):
        """
        Initializes the RegistrationAdapter with the required registration service.

        Args:
            registration_service (RegistrationManagementPort): The domain service for account creation.
        """
        self.registration_service = registration_service

    def render_registration_page(self):
        """
        Renders the registration page to the user.

        Returns:
            str: The rendered HTML for the registration page.
        """
        return render_template("registration.html")

    def register(self):
        """
        Processes the account registration form submission.
        Validates the input using RegistrationRequest DTO and calls the registration service.

        Returns:
            Response: Redirects to login on success, or back to registration on failure.
        """
        submitted_username = request.form.get("username", "")
        submitted_email = request.form.get("email", "")

        try:
            reg_data = RegistrationRequest(
                username=submitted_username,
                email=submitted_email,
                password=request.form.get("password", ""),
                confirm_password=request.form.get("confirm_password", "")
            )
        # Pydantic library exception — caught at web boundary for flash + redirect.
        # Not in blog_exceptions.py. Do not move it there.
        except ValidationError as e:
            for error in e.errors():
                msg = error["msg"].removeprefix("Value error, ")
                flash(_(msg), "error")
            return render_template("registration.html", username=submitted_username, email=submitted_email)

        try:
            self.registration_service.create_account(
                username=reg_data.username,
                password=reg_data.password,
                email=reg_data.email
            )
        except BlogCommentError as e:
            flash(_(str(e)), "error")
            return render_template("registration.html", username=reg_data.username, email=reg_data.email)

        flash(_("Registration successful. Please sign in."), "success")
        return redirect(url_for("auth.login"))
