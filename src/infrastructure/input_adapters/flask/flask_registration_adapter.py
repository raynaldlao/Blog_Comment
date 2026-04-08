from flask import flash, redirect, render_template, request, url_for
from flask.views import MethodView
from pydantic import ValidationError

from src.application.input_ports.registration_management import RegistrationManagementPort
from src.infrastructure.input_adapters.dto.registration_request import RegistrationRequest


class RegistrationAdapter(MethodView):
    """
    Flask Input Adapter (Controller) for Registration operations.
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
        try:
            reg_data = RegistrationRequest(
                username=request.form.get("username", ""),
                email=request.form.get("email", ""),
                password=request.form.get("password", ""),
                confirm_password=request.form.get("confirm_password", "")
            )
        except ValidationError as e:
            for error in e.errors():
                location = str(error["loc"][0]) if error["loc"] else "Request"
                flash(f"{location}: {error['msg']}")
            return redirect(url_for("registration.register"))

        result = self.registration_service.create_account(
            username=reg_data.username,
            password=reg_data.password,
            email=reg_data.email
        )

        if isinstance(result, str):
            flash(result)
            return redirect(url_for("registration.register"))

        flash("Registration successful. Please sign in.")
        return redirect(url_for("auth.login"))
