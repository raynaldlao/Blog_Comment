from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.article_service import ArticleService

article_bp = Blueprint("article", __name__)


@article_bp.route("/")
def list_articles():
    articles = ArticleService.get_all_ordered_by_date()
    return render_template("index.html", articles=articles)


@article_bp.route("/article/<int:article_id>")
def view_article(article_id):
    article = ArticleService.get_by_id(article_id)
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
        ArticleService.create_article(request.form.get("title"), request.form.get("content"), session["user_id"])
        flash("Article published!")
        return redirect(url_for("article.list_articles"))
    return render_template("article_form.html", article=None)


@article_bp.route("/article/<int:article_id>/edit", methods=["GET", "POST"])
def edit_article(article_id):
    if request.method == "POST":
        success = ArticleService.update_article(article_id, session.get("user_id"), session.get("role"), request.form.get("title"), request.form.get("content"))
        if success:
            flash("Article updated!")
            return redirect(url_for("article.view_article", article_id=article_id))
        flash("Update failed: Unauthorized or not found.")
        return redirect(url_for("article.list_articles"))
    article = ArticleService.get_by_id(article_id)
    return render_template("article_form.html", article=article)


@article_bp.route("/article/<int:article_id>/delete")
def delete_article(article_id):
    if ArticleService.delete_article(article_id, session.get("user_id"), session.get("role")):
        flash("Article deleted.")
    else:
        flash("Delete failed.")
    return redirect(url_for("article.list_articles"))
