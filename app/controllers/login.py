from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import Session

from app.models import Account
from database.database_setup import database_engine

login_bp = Blueprint("auth", __name__)

@login_bp.route("/")
def render_login_page():
    return render_template("login.html")


@login_bp.route("/login", methods=["POST"])
def login_authentication():
    username = request.form.get("username")
    password = request.form.get("password")

    with Session(database_engine) as db_session:
        user = Account.authenticate_username_password(db_session, username, password)
        if user:
            session["user_id"] = user.account_id
            session["username"] = user.account_username
            return redirect(url_for("auth.dashboard"))

        flash("Incorrect username or password.")
        return redirect(url_for("auth.render_login_page"))


@login_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.render_login_page"))

    return (
        f"<h1>Welcome {session['username']}</h1>"
        "<a href='/logout'>Logout</a>"
    )


@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.render_login_page"))
