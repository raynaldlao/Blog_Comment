from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import Session

from app.services.article_service import ArticleService
from database.database_setup import database_engine

article_bp = Blueprint("article", __name__)


@article_bp.route("/")
def list_articles():
    with Session(database_engine) as db_session:
        articles = ArticleService.get_all_ordered_by_date(db_session)
        return render_template("index.html", articles=articles)


@article_bp.route("/article/<int:article_id>")
def view_article(article_id):
    with Session(database_engine) as db_session:
        article = ArticleService.get_by_id(db_session, article_id)
        if not article:
            flash("Article not found.")
            return redirect(url_for("article.list_articles"))
        return render_template("article_detail.html", article=article)


@article_bp.route("/article/new", methods=["GET", "POST"])
def create_article():
    if session.get("role") not in ["admin", "author"]:
        flash("Access restricted.")
        return redirect(url_for("article.list_articles"))

    if request.method == "POST":
        with Session(database_engine) as db_session:
            ArticleService.create_article(db_session=db_session, title=request.form.get("title"), content=request.form.get("content"), author_id=session["user_id"])
            flash("Article published!")
            return redirect(url_for("article.list_articles"))

    return render_template("article_form.html", article=None)


@article_bp.route("/article/<int:article_id>/edit", methods=["GET", "POST"])
def edit_article(article_id):
    if session.get("role") not in ["admin", "author"]:
        flash("Access restricted.")
        return redirect(url_for("article.list_articles"))

    with Session(database_engine) as db_session:
        article = ArticleService.get_by_id(db_session, article_id)

        if not ArticleService.can_user_edit_article(article, session.get("user_id"), session.get("role")):
            flash("Permission denied.")
            return redirect(url_for("article.list_articles"))

        if request.method == "POST":
            ArticleService.update_article(db_session=db_session, article=article, title=request.form.get("title"), content=request.form.get("content"))
            flash("Article updated!")
            return redirect(url_for("article.view_article", article_id=article_id))

        return render_template("article_form.html", article=article)


@article_bp.route("/article/<int:article_id>/delete")
def delete_article(article_id):
    with Session(database_engine) as db_session:
        article = ArticleService.get_by_id(db_session, article_id)

        if ArticleService.can_user_edit_article(article, session.get("user_id"), session.get("role")):
            ArticleService.delete_article(db_session, article)
            flash("Article deleted.")
        else:
            flash("Permission denied.")

    return redirect(url_for("article.list_articles"))
