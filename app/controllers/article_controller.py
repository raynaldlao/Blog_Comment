import math

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.wrappers import Response

from app.constants import PaginationConfig, Role, SessionKey
from app.controllers.decorators import roles_accepted
from app.services.article_service import ArticleService
from app.services.comment_service import CommentService
from database.database_setup import db_session

article_bp = Blueprint("article", __name__)


@article_bp.route("/")
def list_articles() -> str:
    """
    Renders the homepage with a paginated list of articles.

    Returns:
        str: The rendered HTML template for the homepage.
    """
    page_number = request.args.get("page", 1, type=int)
    articles_per_page = PaginationConfig.ARTICLES_PER_PAGE

    article_service = ArticleService(db_session)
    articles = article_service.get_paginated_articles(page_number, articles_per_page)
    total_articles = article_service.get_total_count()
    total_pages = math.ceil(total_articles / articles_per_page)

    return render_template(
        "index.html",
        articles=articles,
        page_number=page_number,
        total_pages=total_pages
    )


@article_bp.route("/article/<int:article_id>")
def view_article(article_id: int) -> str | Response:
    """
    Displays the details of a specific article and its comments.

    Args:
        article_id (int): ID of the article to view.

    Returns:
        str | Response: The rendered HTML template for the article or a redirect if the article is not found.
    """
    article_service = ArticleService(db_session)
    article = article_service.get_by_id(article_id)
    if not article:
        flash("Article not found.")
        return redirect(url_for("article.list_articles"))

    comment_service = CommentService(db_session)
    comments = comment_service.get_tree_by_article_id(article_id)
    return render_template("article_detail.html", article=article, comments=comments)


@article_bp.route("/article/new", methods=["GET", "POST"])
@roles_accepted(Role.ADMIN, Role.AUTHOR)
def create_article() -> str | Response:
    """
    Handles the creation of a new blog article.
    Restricted to 'admin' and 'author' roles.

    Returns:
        str | Response: The rendered HTML form (GET) or a redirect to the article list after creation (POST).
    """
    if request.method == "POST":
        article_service = ArticleService(db_session)
        title = str(request.form.get("title") or "")
        content = str(request.form.get("content") or "")
        user_id = int(session.get(SessionKey.USER_ID) or 0)

        article_service.create_article(
            title=title,
            content=content,
            author_id=user_id
        )
        db_session.commit()
        flash("Article published!")
        return redirect(url_for("article.list_articles"))

    return render_template("article_form.html", article=None)


@article_bp.route("/article/<int:article_id>/edit", methods=["GET", "POST"])
@roles_accepted(Role.ADMIN, Role.AUTHOR, Role.USER)
def edit_article(article_id: int) -> str | Response:
    """
    Handles the editing of an existing article.
    Ensures the user is authorized to perform the update.

    Args:
        article_id (int): ID of the article to edit.

    Returns:
        str | Response: The rendered HTML form (GET) or a redirect to the updated article (POST).
    """
    article_service = ArticleService(db_session)

    if request.method == "POST":
        user_id = int(session.get(SessionKey.USER_ID) or 0)
        role = str(session.get(SessionKey.ROLE) or "")
        title = str(request.form.get("title") or "")
        content = str(request.form.get("content") or "")

        article = article_service.update_article(
            article_id=article_id,
            user_id=user_id,
            role=role,
            title=title,
            content=content
        )
        if article:
            db_session.commit()
            flash("Article updated!")
            return redirect(url_for("article.view_article", article_id=article_id))

        flash("Update failed: Unauthorized or not found.")
        return redirect(url_for("article.list_articles"))

    article = article_service.get_by_id(article_id)
    if not article:
        flash("Article not found.")
        return redirect(url_for("article.list_articles"))

    return render_template("article_form.html", article=article)


@article_bp.route("/article/<int:article_id>/delete")
@roles_accepted(Role.ADMIN, Role.AUTHOR, Role.USER)
def delete_article(article_id: int) -> Response:
    """
    Handles the deletion of an article.

    Args:
        article_id (int): ID of the article to delete.

    Returns:
        Response: A redirect to the article list after deletion.
    """
    article_service = ArticleService(db_session)
    user_id = int(session.get(SessionKey.USER_ID) or 0)
    role = str(session.get(SessionKey.ROLE) or "")

    if article_service.delete_article(
        article_id=article_id,
        user_id=user_id,
        role=role
    ):
        db_session.commit()
        flash("Article deleted.")
    else:
        flash("Delete failed: Unauthorized or not found.")

    return redirect(url_for("article.list_articles"))
