from flask import flash, redirect, render_template, request, url_for
from pydantic import ValidationError

from src.application.input_ports.account_session_management import AccountSessionManagement
from src.application.input_ports.article_management import ArticleManagementPort
from src.infrastructure.input_adapters.dto.article_request import ArticleRequest
from src.infrastructure.input_adapters.dto.article_response import ArticleResponse


class ArticleAdapter:
    """
    Flask Input Adapter (Controller) for Article operations.
    Translates web requests into domain operations and renders HTML templates.
    """

    def __init__(
        self,
        article_service: ArticleManagementPort,
        session_service: AccountSessionManagement,
    ):
        self.article_service = article_service
        self.session_service = session_service

    def list_articles(self):
        """Render the blog homepage with paginated articles."""
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
        user = self.session_service.get_current_account()

        return render_template(
            "article_list.html",
            articles=articles,
            current_user=user,
            page=page,
            has_next=has_next,
            has_prev=has_prev
        )

    def read_article(self, article_id: int):
        """Render a single article read view."""
        domain_article = self.article_service.get_by_id(article_id)
        if not domain_article:
            flash("Error: The requested article could not be found.")
            return redirect(url_for("article.list_articles"))

        username = self.article_service.get_author_name(domain_article.article_author_id)
        article = ArticleResponse.from_domain(domain_article, author_username=username)
        user = self.session_service.get_current_account()
        return render_template("article_detail.html", article=article, current_user=user)

    def render_create_page(self):
        """Render the form to write a new article."""
        user = self.session_service.get_current_account()
        if not user:
            flash("You must be signed in to author an article.")
            return redirect(url_for("auth.login"))

        return render_template("article_create.html", current_user=user)

    def create_article(self):
        """Handle the submission of a new article."""
        user = self.session_service.get_current_account()
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

    def render_edit_page(self, article_id: int):
        """Render the form to edit an existing article."""
        user = self.session_service.get_current_account()
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

    def update_article(self, article_id: int):
        """Handle the submission of an article update."""
        user = self.session_service.get_current_account()
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

    def delete_article(self, article_id: int):
        """Handle the deletion of an article."""
        user = self.session_service.get_current_account()
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
