from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.wrappers import Response

from app.constants import SessionKey
from app.services.login_service import LoginService
from database.database_setup import db_session

login_bp = Blueprint("login", __name__)


@login_bp.route("/login-page")
def render_login_page() -> str:
    """
    Renders the login page.

    Returns:
        str: The rendered HTML template for the login page.
    """
    return render_template("login.html")


@login_bp.route("/login", methods=["POST"])
def login_authentication() -> Response:
    """
    Handles user authentication.
    Validates credentials and sets up the session.

    Returns:
        Response: A redirect to the article list on success, or back to the login page on failure.
    """
    login_service = LoginService(db_session)
    username = str(request.form.get("username") or "")
    password = str(request.form.get("password") or "")
    user = login_service.authenticate_user(
        username=username,
        password=password
    )
    if user:
        session[SessionKey.USER_ID] = user.account_id
        session[SessionKey.USERNAME] = user.account_username
        session[SessionKey.ROLE] = user.account_role
        return redirect(url_for("article.list_articles"))

    flash("Incorrect credentials.")
    return redirect(url_for("login.render_login_page"))


@login_bp.route("/logout")
def logout() -> Response:
    """
    Clears the user session and redirects to the article list.

    Returns:
        Response: A redirect to the article list after clearing the session.
    """
    session.clear()
    return redirect(url_for("article.list_articles"))
