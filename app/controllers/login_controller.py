from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.login_service import LoginService

login_bp = Blueprint("login", __name__)


@login_bp.route("/login-page")
def render_login_page():
    return render_template("login.html")


@login_bp.route("/login", methods=["POST"])
def login_authentication():
    user_data = LoginService.authenticate_user(request.form.get("username"), request.form.get("password"))
    if user_data:
        session["user_id"] = user_data["id"]
        session["username"] = user_data["username"]
        session["role"] = user_data["role"]
        return redirect(url_for("article.list_articles"))
    flash("Incorrect credentials.")
    return redirect(url_for("login.render_login_page"))


@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("article.list_articles"))
