from flask import abort, flash, redirect, request, url_for
from flask import g as global_request_context
from flask_babel import gettext as _
from pydantic import ValidationError
from werkzeug.wrappers.response import Response

from blog_exceptions import BlogCommentError
from src.application.domain.account import AccountRole
from src.application.input_ports.comment_management import CommentManagementPort
from src.infrastructure.input_adapters.dto.comment_request import CommentRequest


class CommentAdapter:
    """
    Flask Input Adapter for Comment operations.
    Handles creation, replying, deletion, and listing of comments.
    """

    def __init__(self, comment_service: CommentManagementPort):
        """
        Initializes the adapter with the core port.

        Args:
            comment_service (CommentManagementPort): The domain service for comments.
        """
        self.comment_service = comment_service

    @staticmethod
    def _check_honeypot(article_id: int) -> Response | None:
        """Return a redirect response if the hidden honeypot field is filled.

        Honeypot traps bots that fill invisible form fields. If triggered,
        silently redirect back to the article page so the bot sees success.

        Args:
            article_id: Article ID for the redirect URL.

        Returns:
            Response | None: A redirect response if honeypot triggered,
            otherwise None.
        """
        if request.form.get("hp_comment"):
            return redirect(url_for("article.read_article", article_id=article_id))
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
            flash(_("You must be signed in to post a comment."), "error")
            return redirect(url_for("auth.login"))

        honeypot = self._check_honeypot(article_id)
        if honeypot:
            return honeypot

        try:
            req_data = CommentRequest(content=request.form.get("content", ""))
        # Pydantic library exception — caught at web boundary for flash + redirect.
        # Not in blog_exceptions.py. Do not move it there.
        except ValidationError as e:
            for error in e.errors():
                msg = error["msg"].removeprefix("Value error, ")
                flash(_(msg), "error")
            return redirect(url_for("article.read_article", article_id=article_id))

        remaining = self.comment_service.check_rate_limit(user.account_id)
        if remaining is not None:
            flash(_("You're posting too fast. Please wait %(remaining)ss before posting again.", remaining=remaining), "warning")
            return redirect(url_for("article.read_article", article_id=article_id))

        try:
            self.comment_service.create_comment(
                article_id=article_id,
                user_id=user.account_id,
                content=req_data.content
            )
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Comment added."), "success")

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
            flash(_("You must be signed in to reply."), "error")
            return redirect(url_for("auth.login"))

        honeypot = self._check_honeypot(article_id)
        if honeypot:
            return honeypot

        try:
            req_data = CommentRequest(content=request.form.get("content", ""))
        # Pydantic library exception — caught at web boundary for flash + redirect.
        # Not in blog_exceptions.py. Do not move it there.
        except ValidationError as e:
            for error in e.errors():
                msg = error["msg"].removeprefix("Value error, ")
                flash(_(msg), "error")
            return redirect(url_for("article.read_article", article_id=article_id))

        remaining = self.comment_service.check_rate_limit(user.account_id)
        if remaining is not None:
            flash(_("You're posting too fast. Please wait %(remaining)ss before posting again.", remaining=remaining), "warning")
            return redirect(url_for("article.read_article", article_id=article_id))

        try:
            self.comment_service.create_reply(
                parent_comment_id=parent_comment_id,
                user_id=user.account_id,
                content=req_data.content
            )
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Reply added."), "success")

        return redirect(url_for("article.read_article", article_id=article_id))

    def delete_comment(self, article_id: int, comment_id: int) -> Response:
        """
        Handles soft-deletion of a comment. Author or admin only. Single-click, no confirm-dialog.

        Args:
            article_id (int): ID of the article (for redirection).
            comment_id (int): ID of the comment to delete.

        Returns:
            Response: A redirect to the article detail page.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash(_("You must be signed in to delete comments."), "error")
            return redirect(url_for("auth.login"))

        try:
            self.comment_service.delete_comment(
                comment_id=comment_id,
                user_id=user.account_id,
            )
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Comment deleted."), "success")

        return redirect(url_for("article.read_article", article_id=article_id))

    def edit_comment(self, article_id: int, comment_id: int) -> Response:
        """
        Handles editing a comment's content. Author only (not admin).
        Inline textarea toggle in the template. No rate-limit, no honeypot.

        Args:
            article_id (int): ID of the article (for redirection).
            comment_id (int): ID of the comment to edit.

        Returns:
            Response: A redirect to the article detail page.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash(_("You must be signed in to edit comments."), "error")
            return redirect(url_for("auth.login"))

        content = request.form.get("content", "")
        try:
            self.comment_service.edit_comment(
                comment_id=comment_id,
                user_id=user.account_id,
                content=content,
            )
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Comment updated."), "success")

        return redirect(url_for("article.read_article", article_id=article_id))

    def hard_delete_comment(self, article_id: int, comment_id: int) -> Response:
        """
        Handles permanent hard-deletion of a comment. Admin only.
        Called on already soft-deleted comments to purge them from the database.

        Args:
            article_id (int): ID of the article (for redirection).
            comment_id (int): ID of the comment to permanently delete.

        Returns:
            Response: A redirect to the article detail page.

        Raises:
            403: If the current user is not authenticated as an admin.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash(_("You must be signed in to delete comments."), "error")
            return redirect(url_for("auth.login"))
        if user.account_role != AccountRole.ADMIN:
            abort(403)

        try:
            self.comment_service.hard_delete_comment(
                comment_id=comment_id,
                user_id=user.account_id,
            )
        except BlogCommentError as e:
            flash(_(str(e)), "error")
        else:
            flash(_("Comment permanently deleted."), "success")

        return redirect(url_for("article.read_article", article_id=article_id))
