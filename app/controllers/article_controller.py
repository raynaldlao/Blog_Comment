import math

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.article_service import ArticleService
from app.services.comment_service import CommentService
from database.database_setup import db_session

article_bp = Blueprint("article", __name__)


@article_bp.route("/")
def list_articles():
    current_page_number = 1
    page_number = request.args.get("page", current_page_number, type=int)
    articles_per_page = 10
    article_service = ArticleService(db_session)
    articles = article_service.get_paginated_articles(page_number, articles_per_page)
    total_articles = article_service.get_total_count()
    total_pages = math.ceil(total_articles / articles_per_page)
    return render_template("index.html", articles=articles, page_number=page_number, total_pages=total_pages)


@article_bp.route("/article/<int:article_id>")
def view_article(article_id):
    article_service = ArticleService(db_session)
    article = article_service.get_by_id(article_id)
    if not article:
        flash("Article not found.")
        return redirect(url_for("article.list_articles"))

    comment_service = CommentService(db_session)
    comments = comment_service.get_tree_by_article_id(article_id)
    return render_template("article_detail.html", article=article, comments=comments)


@article_bp.route("/article/new", methods=["GET", "POST"])
def create_article():
    if session.get("role") not in ["admin", "author"]:
        flash("Access restricted.")
        return redirect(url_for("article.list_articles"))
    if request.method == "POST":
        article_service = ArticleService(db_session)
        article_service.create_article(request.form.get("title"), request.form.get("content"), session["user_id"])
        db_session.commit()
        flash("Article published!")
        return redirect(url_for("article.list_articles"))
    return render_template("article_form.html", article=None)


@article_bp.route("/article/<int:article_id>/edit", methods=["GET", "POST"])
def edit_article(article_id):
    if request.method == "POST":
        article_service = ArticleService(db_session)
        article = article_service.update_article(
            article_id,
            session.get("user_id"),
            session.get("role"),
            request.form.get("title"),
            request.form.get("content")
        )
        if article:
            db_session.commit()
            flash("Article updated!")
            return redirect(url_for("article.view_article", article_id=article_id))
        flash("Update failed: Unauthorized or not found.")
        return redirect(url_for("article.list_articles"))
    article_service = ArticleService(db_session)
    article = article_service.get_by_id(article_id)
    if not article:
        flash("Article not found.")
        return redirect(url_for("article.list_articles"))
    return render_template("article_form.html", article=article)


@article_bp.route("/article/<int:article_id>/delete")
def delete_article(article_id):
    article_service = ArticleService(db_session)
    if article_service.delete_article(article_id, session.get("user_id"), session.get("role")):
        db_session.commit()
        flash("Article deleted.")
    else:
        flash("Delete failed.")
    return redirect(url_for("article.list_articles"))
