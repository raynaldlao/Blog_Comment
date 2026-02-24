from flask import Blueprint, flash, redirect, request, session, url_for
from sqlalchemy.orm import Session

from app.models import Article, Comment
from database.database_setup import database_engine

comment_bp = Blueprint("comment", __name__, url_prefix="/comments")


@comment_bp.route("/create/<int:article_id>", methods=["POST"])
def create_comment(article_id):
    if "user_id" not in session:
        flash("You must be logged in to comment.")
        return redirect(url_for("auth.render_login_page"))

    content = request.form.get("content")
    if not content or not content.strip():
        flash("The comment cannot be empty.")
        return redirect(url_for("article.view_article", article_id=article_id))

    with Session(database_engine) as db_session:
        article = Article.get_by_id(db_session, article_id)

        if not article:
            flash("Article not found.")
            return redirect(url_for("article.list_articles"))

        Comment.create_comment(db_session=db_session, article_id=article_id, user_id=session["user_id"], content=content)

    return redirect(url_for("article.view_article", article_id=article_id))


@comment_bp.route("/reply/<int:parent_comment_id>", methods=["POST"])
def reply_to_comment(parent_comment_id):
    if "user_id" not in session:
        flash("You must be logged in to reply.")
        return redirect(url_for("auth.render_login_page"))

    content = request.form.get("content")

    with Session(database_engine) as db_session:
        parent_comment = Comment.get_by_id(db_session, parent_comment_id)

        if not parent_comment:
            flash("The comment you are replying to no longer exists.")
            return redirect(url_for("article.list_articles"))

        article_id = parent_comment.comment_article_id

        if not content or not content.strip():
            flash("The reply cannot be empty.")
            return redirect(url_for("article.view_article", article_id=article_id))

        Comment.create_reply(db_session=db_session, parent_comment_id=parent_comment_id, user_id=session["user_id"], content=content)

    return redirect(url_for("article.view_article", article_id=article_id))


@comment_bp.route("/delete/<int:comment_id>", methods=["GET", "POST"])
def delete_comment(comment_id):
    if session.get("role") != "admin":
        flash("Unauthorized action.")
        return redirect(url_for("article.list_articles"))

    with Session(database_engine) as db_session:
        comment = Comment.get_by_id(db_session, comment_id)

        if comment:
            article_id = comment.comment_article_id
            comment.delete_comment(db_session)
            flash("Comment deleted.")
            return redirect(url_for("article.view_article", article_id=article_id))

    flash("Comment not found.")
    return redirect(url_for("article.list_articles"))
