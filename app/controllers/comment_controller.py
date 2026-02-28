from flask import Blueprint, flash, redirect, request, session, url_for
from werkzeug.wrappers import Response

from app.constants import Role, SessionKey
from app.services.comment_service import CommentService
from app.utils.decorators import login_required, roles_accepted
from database.database_setup import db_session

comment_bp = Blueprint("comment", __name__, url_prefix="/comments")


@comment_bp.route("/create/<int:article_id>", methods=["POST"])
@login_required
def create_comment(article_id: int) -> Response:
    """
    Handles the creation of a new comment on an article.
    Requires the user to be logged in.

    Args:
        article_id (int): ID of the article being commented on.

    Returns:
        Response: A redirect to the article view or login page.
    """
    comment_service = CommentService(db_session)
    content = str(request.form.get("content") or "")
    if comment_service.create_comment(
        article_id=article_id,
        user_id=session[SessionKey.USER_ID],
        content=content
    ):
        db_session.commit()
        flash("Comment added.")
    else:
        flash("Error adding comment.")

    return redirect(url_for("article.view_article", article_id=article_id))


@comment_bp.route("/reply/<int:parent_comment_id>", methods=["POST"])
@login_required
def reply_to_comment(parent_comment_id: int) -> Response:
    """
    Handles the creation of a reply to an existing comment.
    Requires the user to be logged in.

    Args:
        parent_comment_id (int): ID of the comment being replied to.

    Returns:
        Response: A redirect to the article view or the article list in case of error.
    """
    comment_service = CommentService(db_session)
    content = str(request.form.get("content") or "")
    article_id = comment_service.create_reply(
        parent_comment_id=parent_comment_id,
        user_id=session[SessionKey.USER_ID],
        content=content
    )
    if article_id:
        db_session.commit()
        return redirect(url_for("article.view_article", article_id=article_id))

    flash("Error replying.")
    return redirect(url_for("article.list_articles"))


@comment_bp.route("/delete/<int:comment_id>")
@roles_accepted(Role.ADMIN)
def delete_comment(comment_id: int) -> Response:
    """
    Handles the deletion of a comment.
    Restricted to users with the 'admin' role.

    Args:
        comment_id (int): ID of the comment to delete.

    Returns:
        Response: A redirect to the article view or article list after deletion.
    """
    comment_service = CommentService(db_session)
    role = str(session.get(SessionKey.ROLE) or "")
    article_id = comment_service.delete_comment(
        comment_id=comment_id,
        role=role
    )
    if article_id:
        db_session.commit()
        flash("Comment deleted.")
        return redirect(url_for("article.view_article", article_id=article_id))

    flash("Unauthorized or not found.")
    return redirect(url_for("article.list_articles"))
