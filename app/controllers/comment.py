from flask import Blueprint, flash, redirect, request, session, url_for

from app.services.comment_service import CommentService

comment_bp = Blueprint("comment", __name__, url_prefix="/comments")


@comment_bp.route("/create/<int:article_id>", methods=["POST"])
def create_comment(article_id):
    if "user_id" not in session:
        flash("Login required.")
        return redirect(url_for("auth.render_login_page"))
    if CommentService.create_comment(article_id, session["user_id"], request.form.get("content")):
        flash("Comment added.")
    else:
        flash("Error adding comment.")
    return redirect(url_for("article.view_article", article_id=article_id))


@comment_bp.route("/reply/<int:parent_comment_id>", methods=["POST"])
def reply_to_comment(parent_comment_id):
    if "user_id" not in session:
        flash("Login required.")
        return redirect(url_for("auth.render_login_page"))
    article_id = CommentService.create_reply(parent_comment_id, session["user_id"], request.form.get("content"))
    if article_id:
        return redirect(url_for("article.view_article", article_id=article_id))
    flash("Error replying.")
    return redirect(url_for("article.list_articles"))


@comment_bp.route("/delete/<int:comment_id>")
def delete_comment(comment_id):
    article_id = CommentService.delete_comment(comment_id, session.get("role"))
    if article_id:
        flash("Comment deleted.")
        return redirect(url_for("article.view_article", article_id=article_id))
    flash("Unauthorized or not found.")
    return redirect(url_for("article.list_articles"))
