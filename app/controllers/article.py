from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Article, Comment
from database.database_setup import database_engine

article_bp = Blueprint("article", __name__)

@article_bp.route("/")
def list_articles():
    with Session(database_engine) as db_session:
        query = select(Article).order_by(Article.article_published_at.desc())
        articles = db_session.execute(query).scalars().all()
        return render_template("index.html", articles=articles)

@article_bp.route("/article/<int:article_id>")
def view_article(article_id):
    with Session(database_engine) as db_session:
        article = db_session.get(Article, article_id)
        if not article:
            flash("Article not found.")
            return redirect(url_for("article.list_articles"))
        return render_template("article_detail.html", article=article)

@article_bp.route("/article/<int:article_id>/edit", methods=["GET", "POST"])
def edit_article(article_id):
    if session.get("role") not in ["admin", "author"]:
        flash("Access restricted.")
        return redirect(url_for("article.list_articles"))
    with Session(database_engine) as db_session:
        article = db_session.get(Article, article_id)
        if not article or article.article_author_id != session.get("user_id"):
            flash("You can only edit your own articles.")
            return redirect(url_for("article.list_articles"))
        if request.method == "POST":
            article.article_title = request.form.get("title")
            article.article_content = request.form.get("content")
            db_session.commit()
            flash("Article updated successfully!")
            return redirect(url_for("article.view_article", article_id=article_id))
        return render_template("article_form.html", article=article)

@article_bp.route("/article/<int:article_id>/delete")
def delete_article(article_id):
    if session.get("role") not in ["admin", "author"]:
        flash("Permission denied.")
        return redirect(url_for("article.list_articles"))
    with Session(database_engine) as db_session:
        article = db_session.get(Article, article_id)
        if article:
            if article.article_author_id == session.get("user_id") or session.get("role") == "admin":
                db_session.delete(article)
                db_session.commit()
                flash("Article deleted.")
            else:
                flash("Permission denied.")
    return redirect(url_for("article.list_articles"))

@article_bp.route("/article/new", methods=["GET", "POST"])
def create_article():
    if session.get("role") not in ["admin", "author"]:
        flash("Access restricted.")
        return redirect(url_for("article.list_articles"))
    if request.method == "POST":
        with Session(database_engine) as db_session:
            new_art = Article(
                article_title=request.form.get("title"),
                article_content=request.form.get("content"),
                article_author_id=session["user_id"]
            )
            db_session.add(new_art)
            db_session.commit()
            flash("Article published!")
            return redirect(url_for("article.list_articles"))
    return render_template("article_form.html", article=None)

@article_bp.route("/article/<int:article_id>/comment", methods=["POST"])
def post_comment(article_id):
    if "user_id" not in session:
        flash("Log in to comment.")
        return redirect(url_for("auth.render_login_page"))
    with Session(database_engine) as db_session:
        new_comment = Comment(
            comment_article_id=article_id,
            comment_written_account_id=session["user_id"],
            comment_content=request.form.get("content"),
            comment_reply_to=int(request.form.get("reply_to")) if request.form.get("reply_to") else None
        )
        db_session.add(new_comment)
        db_session.commit()
    return redirect(url_for("article.view_article", article_id=article_id))

@article_bp.route("/comment/<int:comment_id>/delete")
def delete_comment(comment_id):
    if session.get("role") != "admin":
        flash("Only admins can delete comments.")
        return redirect(request.referrer or url_for("article.list_articles"))
    with Session(database_engine) as db_session:
        comment = db_session.get(Comment, comment_id)
        if comment:
            article_id = comment.comment_article_id
            db_session.delete(comment)
            db_session.commit()
            flash("Comment deleted.")
            return redirect(url_for("article.view_article", article_id=article_id))
    return redirect(url_for("article.list_articles"))
