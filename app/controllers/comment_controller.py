from flask import Blueprint, flash, redirect, request, session, url_for

from app.services.comment_service import CommentService
from database.database_setup import db_session

comment_bp = Blueprint("comment", __name__, url_prefix="/comments")


@comment_bp.route("/create/<int:article_id>", methods=["POST"])
def create_comment(article_id):
    # Exception to add here
    if not session.get("user_id"):
        flash("Login required.")
        return redirect(url_for("login.render_login_page"))
    comment_service = CommentService(db_session)
    if comment_service.create_comment(article_id, session["user_id"], request.form.get("content")):
        db_session.commit()
        flash("Comment added.")
    else:
        flash("Error adding comment.")
    return redirect(url_for("article.view_article", article_id=article_id))


@comment_bp.route("/reply/<int:parent_comment_id>", methods=["POST"])
def reply_to_comment(parent_comment_id):
    # Exception to add here
    if not session.get("user_id"):
        flash("Login required.")
        return redirect(url_for("login.render_login_page"))

    comment_service = CommentService(db_session)
    article_id = comment_service.create_reply(parent_comment_id, session["user_id"], request.form.get("content"))
    if article_id:
        db_session.commit()
        return redirect(url_for("article.view_article", article_id=article_id))

    flash("Error replying.")
    return redirect(url_for("article.list_articles"))


@comment_bp.route("/delete/<int:comment_id>")
def delete_comment(comment_id):
    comment_service = CommentService(db_session)
    article_id = comment_service.delete_comment(comment_id, session.get("role"))
    if article_id:
        db_session.commit()
        flash("Comment deleted.")
        return redirect(url_for("article.view_article", article_id=article_id))

    flash("Unauthorized or not found.")
    return redirect(url_for("article.list_articles"))
