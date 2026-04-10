from flask import Response, flash, redirect, request, url_for
from flask import g as global_request_context
from pydantic import ValidationError

from src.application.input_ports.comment_management import CommentManagementPort
from src.infrastructure.input_adapters.dto.comment_request import CommentRequest


class CommentAdapter:
    """
    Flask Input Adapter (Controller) for Comment operations.
    Handles creation, replying, deletion, and listing of comments.
    """

    def __init__(self, comment_service: CommentManagementPort):
        """
        Initializes the adapter with the core port.

        Args:
            comment_service (CommentManagementPort): The domain service for comments.
        """
        self.comment_service = comment_service

    def create_comment(self, article_id: int) -> Response:
        """
        Handles the creation of a new top-level comment on an article.

        Args:
            article_id (int): ID of the article being commented on.

        Returns:
            Response: A redirect to the article detail page.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash("You must be signed in to post a comment.")
            return redirect(url_for("auth.login"))

        try:
            req_data = CommentRequest(content=request.form.get("content", ""))
        except ValidationError as e:
            for error in e.errors():
                flash(f"Validation Error: {error['msg']}")
            return redirect(url_for("article.read_article", article_id=article_id))

        result = self.comment_service.create_comment(
            article_id=article_id,
            user_id=user.account_id,
            content=req_data.content
        )

        if isinstance(result, str):
            flash(result)
        else:
            flash("Comment added.")

        return redirect(url_for("article.read_article", article_id=article_id))

    def reply_to_comment(self, article_id: int, parent_comment_id: int) -> Response:
        """
        Handles the creation of a reply to an existing comment.

        Args:
            article_id (int): ID of the article (for redirection).
            parent_comment_id (int): ID of the parent comment.

        Returns:
            Response: A redirect to the article detail page.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash("You must be signed in to reply.")
            return redirect(url_for("auth.login"))

        try:
            req_data = CommentRequest(content=request.form.get("content", ""))
        except ValidationError as e:
            for error in e.errors():
                flash(f"Validation Error: {error['msg']}")
            return redirect(url_for("article.read_article", article_id=article_id))

        result = self.comment_service.create_reply(
            parent_comment_id=parent_comment_id,
            user_id=user.account_id,
            content=req_data.content
        )

        if isinstance(result, str):
            flash(result)
        else:
            flash("Reply added.")

        return redirect(url_for("article.read_article", article_id=article_id))

    def delete_comment(self, article_id: int, comment_id: int) -> Response:
        """
        Handles the deletion of a comment (Admin only).

        Args:
            article_id (int): ID of the article (for redirection).
            comment_id (int): ID of the comment to delete.

        Returns:
            Response: A redirect to the article detail page.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash("You must be signed in to delete comments.")
            return redirect(url_for("auth.login"))

        result = self.comment_service.delete_comment(
            comment_id=comment_id,
            user_id=user.account_id
        )

        if isinstance(result, str):
            flash(result)
        elif result is True:
            flash("Comment deleted.")
        else:
            flash("Unauthorized or error.")

        return redirect(url_for("article.read_article", article_id=article_id))
