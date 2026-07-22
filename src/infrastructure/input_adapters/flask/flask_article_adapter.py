import json
import math

from pydantic import ValidationError
from werkzeug.wrappers.response import Response

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask import g as global_request_context
from src.application.domain.comment import CommentNode
from src.application.input_ports.article_management import ArticleManagementPort
from src.infrastructure.input_adapters.dto.article_request import ArticleRequest
from src.infrastructure.input_adapters.dto.article_response import ArticleResponse
from src.infrastructure.input_adapters.dto.comment_response import CommentResponse


class ArticleAdapter:
    """
    Flask Input Adapter for Article operations.
    Translates web requests into domain operations and renders HTML templates.

    This adapter adheres strictly to Rule #6 (1 Adapter = 1 Port) by depending
    exclusively on ArticleManagementPort. Session context is retrieved via global_request_context.
    """

    def __init__(self, article_service: ArticleManagementPort):
        """
        Initializes the ArticleAdapter with its primary domain port.

        Args:
            article_service (ArticleManagementPort): The core service for articles.
        """
        self.article_service = article_service

    @staticmethod
    def _count_comment_nodes(nodes: list[CommentNode]) -> int:
        """
        Recursively count all comment nodes in the nested tree.

        Soft-deleted comments are included since they persist as placeholders.
        Hard-deleted comments are absent from the tree, thus not counted.

        Args:
            nodes: list of CommentNode domain objects.

        Returns:
            Total number of comments including nested replies.
        """
        count = len(nodes)
        for node in nodes:
            count += ArticleAdapter._count_comment_nodes(node.replies)
        return count

    def list_articles(self) -> str:
        """
        Renders the blog homepage with a paginated list of articles.
        Supports an optional "q" query parameter for searching articles
        by title or description.

        Retrieves the current user from global_request_context for UI
        conditional rendering.

        Returns:
            str: The rendered HTML content of the 'article_list.html' template.
        """
        query = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)

        if query:
            domain_articles = self.article_service.search_articles(query, page=page, per_page=10)
            total_count = self.article_service.count_search(query)
        else:
            domain_articles = self.article_service.get_paginated_articles(page=page, per_page=10)
            total_count = self.article_service.get_total_count()

        articles = []

        for item in domain_articles:
            articles.append(ArticleResponse.from_domain(
                item.article,
                author_username=item.author_name,
                author_avatar_file_id=item.author_avatar_file_id,
            ))

        has_next = (page * 10) < total_count
        has_prev = page > 1
        total_pages = math.ceil(total_count / 10)
        user = global_request_context.get("current_user")

        return render_template(
            "article_list.html",
            articles=articles,
            current_user=user,
            page=page,
            has_next=has_next,
            has_prev=has_prev,
            total_pages=total_pages,
            query=query,
        )

    def read_article(self, article_id: int) -> str | Response:
        """
        Renders the detailed view of a single article, including its comments.
        Composition is handled at the service layer to respect port isolation.

        Args:
            article_id (int): The unique identifier of the article to read.

        Returns:
            Union[str, Response]: The 'article_detail.html' template or a redirect to the list view.
        """
        result = self.article_service.get_article_with_comments(article_id)
        if isinstance(result, str):
            flash(f"Error: {result}", "error")
            return redirect(url_for("article.list_articles"))

        detail = result
        article = ArticleResponse.from_domain(
            detail.article_with_author.article,
            author_username=detail.article_with_author.author_name,
            author_avatar_file_id=detail.article_with_author.author_avatar_file_id,
        )

        content = article.article_content
        try:
            json.loads(content)
        except (json.JSONDecodeError, TypeError):
            content = json.dumps([{
                "type": "paragraph",
                "content": [{"type": "text", "text": content}]
            }])

        dto_comments = CommentResponse.map_nested_tree(detail.nested_comments)
        user = global_request_context.get("current_user")
        return render_template(
            "article_detail.html",
            article=article,
            article_content_json=content,
            nested_comments=dto_comments,
            comment_count=self._count_comment_nodes(detail.nested_comments),
            current_user=user,
            page_with_editor=True,
            page_with_comments=True,
        )

    def render_create_page(self) -> str | Response:
        """
        Renders the form to author a new article.
        Requires the user to be signed in (checked via global_request_context).

        Returns:
            Union[str, Response]: The 'article_create.html' form or a redirect to the login page.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash("You must be signed in to author an article.", "error")
            return redirect(url_for("auth.login"))

        if user.account_role not in ["admin", "author"]:
            flash("Insufficient permissions: Only authors or admins can create articles.", "error")
            return redirect(url_for("article.list_articles"))

        return render_template("article_create.html", current_user=user, page_with_editor=True)

    def api_get_article(self, article_id: int) -> Response | tuple[Response, int]:
        """
        Handles JSON API request for fetching a single article.
        Wraps legacy plain-text content into a BlockNote paragraph block
        for compatibility with the React viewer.

        Args:
            article_id (int): The unique identifier of the article to retrieve.

        Returns:
            Response | tuple[Response, int]: A JSON response with article data
            and HTTP 200 on success, or an error JSON with HTTP 404
            on failure.
        """
        article = self.article_service.get_by_id(article_id)
        if not article:
            return jsonify({"error": "Article not found."}), 404

        content = article.article_content
        try:
            json.loads(content)
        except (json.JSONDecodeError, TypeError):
            content = json.dumps([{
                "type": "paragraph",
                "content": [{"type": "text", "text": content}]
            }])

        username = self.article_service.get_author_name(article.article_author_id)
        return jsonify({
            "id": article.article_id,
            "title": article.article_title,
            "description": article.article_description,
            "content": content,
            "author_id": article.article_author_id,
            "author_username": username,
            "published_at": article.article_published_at,
            "article_edited_at": article.article_edited_at,
        })

    def api_create_article(self) -> Response | tuple[Response, int]:
        """
        Handles JSON API request for creating a new article.
        Validates authentication, authorization, and input data,
        then delegates creation to the article service.

        Returns:
            Response | tuple[Response, int]: A JSON response with the new
            article id and HTTP 201 on success, or an error JSON with
            HTTP 400/401/403 on failure.
        """
        user = global_request_context.get("current_user")
        if not user:
            return jsonify({"error": "Unauthorized."}), 401
        if user.account_role not in ["admin", "author"]:
            return jsonify({"error": "Insufficient permissions."}), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON body."}), 400

        try:
            req_data = ArticleRequest(
                title=data.get("title", ""),
                content=data.get("content", ""),
                description=data.get("description", ""),
            )
        except ValidationError as e:
            for error in e.errors():
                return jsonify({"error": f"({error['loc'][0]}): {error['msg']}"}), 400
            return jsonify({"error": "Validation error."}), 400

        result = self.article_service.create_article(
            title=req_data.title, content=req_data.content,
            author_id=user.account_id, author_role=user.account_role,
            description=req_data.description,
        )
        if isinstance(result, str):
            return jsonify({"error": result}), 403

        return jsonify({"id": result.article_id}), 201

    def api_update_article(self, article_id: int) -> Response | tuple[Response, int]:
        """
        Handles JSON API request for updating an existing article.
        Validates authentication, authorization, and input data,
        then delegates the update to the article service.

        Args:
            article_id (int): The unique identifier of the article to update.

        Returns:
            Response | tuple[Response, int]: A JSON response with OK
            and HTTP 200 on success, or an error JSON with
            HTTP 400/401/403 on failure.
        """
        user = global_request_context.get("current_user")
        if not user:
            return jsonify({"error": "Unauthorized."}), 401
        if user.account_role not in ["admin", "author"]:
            return jsonify({"error": "Insufficient permissions."}), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON body."}), 400

        try:
            req_data = ArticleRequest(
                title=data.get("title", ""),
                content=data.get("content", ""),
                description=data.get("description", ""),
            )
        except ValidationError as e:
            for error in e.errors():
                return jsonify({"error": f"({error['loc'][0]}): {error['msg']}"}), 400
            return jsonify({"error": "Validation error."}), 400

        result = self.article_service.update_article(
            article_id=article_id, user_id=user.account_id,
            title=req_data.title, content=req_data.content,
            description=req_data.description,
        )
        if isinstance(result, str):
            return jsonify({"error": result}), 403

        return jsonify({"ok": True})

    def _api_delete_article(self, article_id: int) -> Response | tuple[Response, int]:
        """
        Handles JSON API request for article deletion.
        Validates authentication and authorization, then delegates
        deletion to the article service.

        Args:
            article_id (int): The unique identifier of the article to delete.

        Returns:
            Response | tuple[Response, int]: A JSON response with OK
            and HTTP 200 on success, or an error JSON with HTTP 401/403
            on failure.
        """
        user = global_request_context.get("current_user")
        if not user:
            return jsonify({"error": "Unauthorized."}), 401
        if user.account_role not in ["admin", "author"]:
            return jsonify({"error": "Insufficient permissions."}), 403

        result = self.article_service.delete_article(
            article_id=article_id, user_id=user.account_id,
        )
        if isinstance(result, str):
            return jsonify({"error": result}), 403

        return jsonify({"ok": True})

    def delete_article_html(self, article_id: int) -> Response:
        """
        Handles HTML form submission for article deletion.
        Authenticates the user, delegates to the private API layer,
        and redirects to the article list with a flash message.

        Args:
            article_id (int): The unique identifier of the article to delete.

        Returns:
            Response: A redirect to the login page or article list view.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash("You must be logged in to delete articles.", "error")
            return redirect(url_for("auth.login"))

        result = self._api_delete_article(article_id)

        if isinstance(result, tuple):
            flash(result[0].get_json()["error"], "error")
        else:
            flash("Article deleted successfully.", "success")

        return redirect(url_for("article.list_articles"))

    def render_edit_page(self, article_id: int) -> str | Response:
        """
        Renders the edit form for an existing article.
        Verifies article existence before rendering.

        Args:
            article_id (int): The unique identifier of the article to edit.

        Returns:
            Union[str, Response]: The 'article_edit.html' form or a redirect to the list view.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash("You must be signed in to edit an article.", "error")
            return redirect(url_for("auth.login"))

        if user.account_role not in ["admin", "author"]:
            flash("Insufficient permissions: Only authors or admins can create articles.", "error")
            return redirect(url_for("article.list_articles"))

        domain_article = self.article_service.get_by_id(article_id)
        if not domain_article:
            flash("Error: The requested article could not be found.", "error")
            return redirect(url_for("article.list_articles"))

        if user.account_role != "admin" and domain_article.article_author_id != user.account_id:
            flash("You do not have permission to edit this article.", "error")
            return redirect(url_for("article.list_articles"))

        username = self.article_service.get_author_name(domain_article.article_author_id)
        article = ArticleResponse.from_domain(domain_article, author_username=username)
        return render_template("article_edit.html", article=article, current_user=user, page_with_editor=True)
