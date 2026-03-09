from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.wrappers import Response

from app.services.registration_service import RegistrationService
from database.database_setup import db_session

registration_bp = Blueprint("registration", __name__)


@registration_bp.route("/registration-page")
def render_registration_page() -> str:
    """
    Renders the registration page.

    Returns:
        str: The rendered HTML template for the registration page.
    """
    return render_template("registration.html")


@registration_bp.route("/create-account", methods=["POST"])
def submit_registration_form() -> Response:
    """
    Handles user account creation.

    Returns:
        Response: A redirect back to the login page with a success
        or error flash message.
    """
    registration_service = RegistrationService(db_session)
    username = str(request.form.get("username") or "")
    password = str(request.form.get("password") or "")
    email = str(request.form.get("email") or "")

    result = registration_service.create_account(
        username=username, password=password, email=email
    )

    if isinstance(result, str):
        flash(result)
        return redirect(url_for("registration.render_registration_page"))

    flash("Account created successfully.")
    return redirect(url_for("login.render_login_page"))
