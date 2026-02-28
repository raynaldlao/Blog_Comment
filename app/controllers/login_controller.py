from flask import Blueprint, Response, flash, redirect, render_template, request, session, url_for

from app.services.login_service import LoginService
from database.database_setup import db_session

login_bp = Blueprint("login", __name__)


@login_bp.route("/login-page")
def render_login_page() -> str:
    """
    Renders the login page.

    Returns:
        str: Rendered HTML template.
    """
    return render_template("login.html")


@login_bp.route("/login", methods=["POST"])
def login_authentication() -> Response:
    """
    Handles user authentication.
    Validates credentials and sets up the session.

    Returns:
        Response: Redirect to the article list on success, or login page on failure.
    """
    login_service = LoginService(db_session)
    user = login_service.authenticate_user(request.form.get("username"), request.form.get("password"))
    if user:
        session["user_id"] = user.account_id
        session["username"] = user.account_username
        session["role"] = user.account_role
        return redirect(url_for("article.list_articles"))
    flash("Incorrect credentials.")
    return redirect(url_for("login.render_login_page"))


@login_bp.route("/logout")
def logout() -> Response:
    """
    Clears the user session and redirects to the article list.

    Returns:
        Response: Redirect to the article list.
    """
    session.clear()
    return redirect(url_for("article.list_articles"))
