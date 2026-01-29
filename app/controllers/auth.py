from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Account

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def login_page():
    return render_template("login.html")

@auth_bp.route("/login", methods=["POST"])
def login_handler():
    username = request.form.get("username")
    password = request.form.get("password")

    with Session(engine) as db_session:
        stmt = select(Account).where(Account.account_username == username)
        user = db_session.execute(stmt).scalar_one_or_none()

        if user and user.account_password == password:
            session["user_id"] = user.account_id
            session["username"] = user.account_username
            return redirect(url_for("auth.dashboard"))

        flash("Identifiants incorrects")
        return redirect(url_for("auth.login_page"))

@auth_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect(url_for("auth.login_page"))
    return f"<h1>Bienvenue {session['username']}</h1><a href='/logout'>Déconnexion</a>"

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))
