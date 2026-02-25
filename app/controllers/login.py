from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import Session

from app.services.login_service import LoginService
from database.database_setup import database_engine

login_bp = Blueprint("auth", __name__)


@login_bp.route("/login-page")
def render_login_page():
    return render_template("login.html")


@login_bp.route("/login", methods=["POST"])
def login_authentication():
    username = request.form.get("username")
    password = request.form.get("password")

    with Session(database_engine) as db_session:
        user = LoginService.authenticate_user(db_session, username, password)
        if user:
            session["user_id"] = user.account_id
            session["username"] = user.account_username
            session["role"] = user.account_role
            return redirect(url_for("article.list_articles"))

        flash("Incorrect username or password.")
        return redirect(url_for("auth.render_login_page"))


@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("article.list_articles"))
