
from flask import Response, flash, redirect, render_template, request, url_for
from flask import g as global_request_context
from pydantic import ValidationError

from src.application.input_ports.article_management import ArticleManagementPort
from src.infrastructure.input_adapters.dto.article_request import ArticleRequest
from src.infrastructure.input_adapters.dto.article_response import ArticleResponse
from src.infrastructure.input_adapters.dto.comment_response import CommentResponse


class ArticleAdapter:
    """
    Flask Input Adapter (Controller) for Article operations.
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

    def list_articles(self) -> str:
        """
        Renders the blog homepage with a paginated list of articles.
        Retrieves the current user from global_request_context for UI conditional rendering.

        Returns:
            str: The rendered HTML content of the 'article_list.html' template.
        """
        page = request.args.get("page", 1, type=int)
        domain_articles = self.article_service.get_paginated_articles(page=page)
        total_count = self.article_service.get_total_count()
        author_names = {}
        articles = []

        for a in domain_articles:
            if a.article_author_id not in author_names:
                author_names[a.article_author_id] = self.article_service.get_author_name(a.article_author_id)
            articles.append(ArticleResponse.from_domain(a, author_username=author_names[a.article_author_id]))

        has_next = (page * 10) < total_count
        has_prev = page > 1
        user = global_request_context.get("current_user")

        return render_template(
            "article_list.html",
            articles=articles,
            current_user=user,
            page=page,
            has_next=has_next,
            has_prev=has_prev
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
            flash(f"Error: {result}")
            return redirect(url_for("article.list_articles"))

        domain_article, threaded_comments = result
        username = self.article_service.get_author_name(domain_article.article_author_id)
        article = ArticleResponse.from_domain(domain_article, author_username=username)
        dto_comments = {}
        for key, comments in threaded_comments.items():
            dto_comments[key] = [CommentResponse.from_domain(c) for c in comments]

        user = global_request_context.get("current_user")
        return render_template(
            "article_detail.html",
            article=article,
            threaded_comments=dto_comments,
            current_user=user
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
            flash("You must be signed in to author an article.")
            return redirect(url_for("auth.login"))

        return render_template("article_create.html", current_user=user)

    def create_article(self) -> Response:
        """
        Processes the submission of a new article.
        Validates input via ArticleRequest DTO and passes IDs to the domain service.

        Returns:
            Response: A redirect to the new article's detail page or back to the form on error.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash("You must be signed in to author an article.")
            return redirect(url_for("auth.login"))

        try:
            req_data = ArticleRequest(
                title=request.form.get("title", ""),
                content=request.form.get("content", ""),
            )
        except ValidationError as e:
            for error in e.errors():
                flash(f"Validation Error ({error['loc'][0]}): {error['msg']}")
            return redirect(url_for("article.render_create_page"))

        result = self.article_service.create_article(
            title=req_data.title,
            content=req_data.content,
            author_id=user.account_id,
            author_role=user.account_role,
        )

        if isinstance(result, str):
            flash(result)
            return redirect(url_for("article.render_create_page"))

        flash("Your article has been successfully published!")
        return redirect(url_for("article.read_article", article_id=result.article_id))

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
            flash("You must be signed in to edit an article.")
            return redirect(url_for("auth.login"))

        domain_article = self.article_service.get_by_id(article_id)
        if not domain_article:
            flash("Error: The requested article could not be found.")
            return redirect(url_for("article.list_articles"))

        username = self.article_service.get_author_name(domain_article.article_author_id)
        article = ArticleResponse.from_domain(domain_article, author_username=username)
        return render_template("article_edit.html", article=article, current_user=user)

    def update_article(self, article_id: int) -> Response:
        """
        Processes an article update request.
        Passes the current user ID to the service for ownership verification.

        Args:
            article_id (int): ID of the article to update.

        Returns:
            Response: A redirect to the detail page or back to the edit form on error.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash("You must be signed in to edit an article.")
            return redirect(url_for("auth.login"))

        try:
            req_data = ArticleRequest(
                title=request.form.get("title", ""),
                content=request.form.get("content", ""),
            )
        except ValidationError as e:
            for error in e.errors():
                flash(f"Validation Error ({error['loc'][0]}): {error['msg']}")
            return redirect(url_for("article.render_edit_page", article_id=article_id))

        result = self.article_service.update_article(
            article_id=article_id,
            user_id=user.account_id,
            title=req_data.title,
            content=req_data.content,
        )

        if isinstance(result, str):
            flash(result)
            return redirect(url_for("article.render_edit_page", article_id=article_id))

        flash("Your article has been successfully updated!")
        return redirect(url_for("article.read_article", article_id=article_id))

    def delete_article(self, article_id: int) -> Response:
        """
        Processes an article deletion request.
        Ownership or Admin permissions are verified at the domain service level.

        Args:
            article_id (int): ID of the article to delete.

        Returns:
            Response: A redirect to the articles list page.
        """
        user = global_request_context.get("current_user")
        if not user:
            flash("You must be signed in to delete an article.")
            return redirect(url_for("auth.login"))

        result = self.article_service.delete_article(
            article_id=article_id,
            user_id=user.account_id
        )

        if isinstance(result, str):
            flash(result)
            return redirect(url_for("article.read_article", article_id=article_id))

        flash("Article has been successfully deleted.")
        return redirect(url_for("article.list_articles"))
