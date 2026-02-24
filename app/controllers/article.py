from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import Session

from app.models import Article
from database.database_setup import database_engine

article_bp = Blueprint("article", __name__)


@article_bp.route("/")
def list_articles():
    with Session(database_engine) as db_session:
        articles = Article.get_all_ordered_by_date(db_session)
        return render_template("index.html", articles=articles)


@article_bp.route("/article/<int:article_id>")
def view_article(article_id):
    with Session(database_engine) as db_session:
        article = Article.get_by_id(db_session, article_id)

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
            Article.create_article(db_session=db_session, title=request.form.get("title"), content=request.form.get("content"), author_id=session["user_id"])
            flash("Article published!")
            return redirect(url_for("article.list_articles"))

    return render_template("article_form.html", article=None)


@article_bp.route("/article/<int:article_id>/edit", methods=["GET", "POST"])
def edit_article(article_id):
    if session.get("role") not in ["admin", "author"]:
        flash("Access restricted.")
        return redirect(url_for("article.list_articles"))

    with Session(database_engine) as db_session:
        article = Article.get_by_id(db_session, article_id)

        if not article or not article.is_editable_by(session.get("user_id"), session.get("role")):
            flash("You can only edit your own articles.")
            return redirect(url_for("article.list_articles"))

        if request.method == "POST":
            article.update_article(db_session=db_session, title=request.form.get("title"), content=request.form.get("content"))
            flash("Article updated successfully!")
            return redirect(url_for("article.view_article", article_id=article_id))

        return render_template("article_form.html", article=article)


@article_bp.route("/article/<int:article_id>/delete")
def delete_article(article_id):
    if session.get("role") not in ["admin", "author"]:
        flash("Permission denied.")
        return redirect(url_for("article.list_articles"))

    with Session(database_engine) as db_session:
        article = Article.get_by_id(db_session, article_id)

        if article and article.is_editable_by(session.get("user_id"), session.get("role")):
            article.delete_article(db_session)
            flash("Article deleted.")
        else:
            flash("Permission denied or article not found.")

    return redirect(url_for("article.list_articles"))
