from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import database_engine
from app.models import Account

login_bp = Blueprint("auth", __name__)

@login_bp.route("/")
def render_login_page():
    return render_template("login.html")


@login_bp.route("/login", methods=["POST"])
def login_authentication():
    username = request.form.get("username")
    password = request.form.get("password")

    with Session(database_engine) as db_session:
        query = select(Account).where(Account.account_username == username)
        user = db_session.execute(query).scalar_one_or_none()

        if user and user.account_password == password:
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
