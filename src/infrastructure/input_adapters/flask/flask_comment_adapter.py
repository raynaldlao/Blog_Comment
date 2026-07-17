import time

from pydantic import ValidationError
from werkzeug.wrappers.response import Response

from flask import flash, redirect, request, url_for
from flask import g as global_request_context
from src.application.input_ports.comment_management import CommentManagementPort
from src.infrastructure.input_adapters.dto.comment_request import CommentRequest


class CommentAdapter:
    """
    Flask Input Adapter for Comment operations.
    Handles creation, replying, deletion, and listing of comments.
    """

    COMMENT_INTERVAL = 60

    def __init__(self, comment_service: CommentManagementPort):
        """
        Initializes the adapter with the core port.

        Args:
            comment_service (CommentManagementPort): The domain service for comments.
        """
        self.comment_service = comment_service
        self._user_comment_timestamps: dict[int, float] = {}

    def _check_comment_rate_limit(self, user_id: int) -> int | None:
        """
        Checks if the user is posting comments too fast.

        Returns number of remaining seconds to wait, or None if allowed.

        Args:
            user_id (int): The identifier of the user to check.

        Returns:
            int | None: Remaining cooldown seconds, or None if the user can post.
        """
        now = time.time()
        last = self._user_comment_timestamps.get(user_id)
        if last:
            elapsed = now - last
            if elapsed < self.COMMENT_INTERVAL:
                return max(1, int(self.COMMENT_INTERVAL - elapsed))
        self._user_comment_timestamps[user_id] = now
        return None

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
            flash("You must be signed in to post a comment.", "error")
            return redirect(url_for("auth.login"))

        if request.form.get("hp_comment"):
            return redirect(url_for("article.read_article", article_id=article_id))

        try:
            req_data = CommentRequest(content=request.form.get("content", ""))
        except ValidationError as e:
            for error in e.errors():
                msg = error["msg"].removeprefix("Value error, ")
                flash(msg, "error")
            return redirect(url_for("article.read_article", article_id=article_id))

        remaining = self._check_comment_rate_limit(user.account_id)
        if remaining is not None:
            flash(f"You're posting too fast. Please wait {remaining}s before posting again.", "warning")
            return redirect(url_for("article.read_article", article_id=article_id))

        result = self.comment_service.create_comment(
            article_id=article_id,
            user_id=user.account_id,
            content=req_data.content
        )

        if isinstance(result, str):
            flash(result, "error")
        else:
            flash("Comment added.", "success")

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
            flash("You must be signed in to reply.", "error")
            return redirect(url_for("auth.login"))

        if request.form.get("hp_comment"):
            return redirect(url_for("article.read_article", article_id=article_id))

        try:
            req_data = CommentRequest(content=request.form.get("content", ""))
        except ValidationError as e:
            for error in e.errors():
                msg = error["msg"].removeprefix("Value error, ")
                flash(msg, "error")
            return redirect(url_for("article.read_article", article_id=article_id))

        remaining = self._check_comment_rate_limit(user.account_id)
        if remaining is not None:
            flash(f"You're posting too fast. Please wait {remaining}s before posting again.", "warning")
            return redirect(url_for("article.read_article", article_id=article_id))

        result = self.comment_service.create_reply(
            parent_comment_id=parent_comment_id,
            user_id=user.account_id,
            content=req_data.content
        )

        if isinstance(result, str):
            flash(result, "error")
        else:
            flash("Reply added.", "success")

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
            flash("You must be signed in to delete comments.", "error")
            return redirect(url_for("auth.login"))

        result = self.comment_service.delete_comment(
            comment_id=comment_id,
            user_id=user.account_id,
        )

        if isinstance(result, str):
            flash(result, "error")
        elif result is True:
            flash("Comment deleted.", "success")
        else:
            flash("Unauthorized or error.", "error")

        return redirect(url_for("article.read_article", article_id=article_id))
