from flask import Flask


def _register_article_routes(app: Flask, adapters: dict) -> None:
    art = adapters["article_adapter"]
    app.add_url_rule("/", view_func=art.list_articles, endpoint="article.list_articles")
    app.add_url_rule("/articles/<int:article_id>", view_func=art.read_article, endpoint="article.read_article")
    app.add_url_rule("/articles/new", view_func=art.render_create_page, methods=["GET"], endpoint="article.render_create_page")
    app.add_url_rule(
        "/articles/<int:article_id>/edit", view_func=art.render_edit_page, methods=["GET"], endpoint="article.render_edit_page"
    )
    app.add_url_rule(
        "/articles/<int:article_id>/delete",
        view_func=art.delete_article_html,
        methods=["POST"],
        endpoint="article.delete_article_html",
    )


def _register_article_api_routes(app: Flask, adapters: dict) -> None:
    art = adapters["article_adapter"]
    csrf = app.extensions["csrf"]

    app.add_url_rule(
        "/api/articles/<int:article_id>",
        view_func=art.api_get_article, methods=["GET"],
        endpoint="article.api_get",
    )
    csrf.exempt(art.api_get_article)

    app.add_url_rule(
        "/api/articles",
        view_func=art.api_create_article, methods=["POST"],
        endpoint="article.api_create",
    )
    csrf.exempt(art.api_create_article)

    app.add_url_rule(
        "/api/articles/<int:article_id>",
        view_func=art.api_update_article, methods=["PUT"],
        endpoint="article.api_update",
    )
    csrf.exempt(art.api_update_article)

    app.add_url_rule(
        "/api/articles/<int:article_id>",
        view_func=art._api_delete_article, methods=["DELETE"],
        endpoint="article.api_delete",
    )
    csrf.exempt(art._api_delete_article)


def _register_comment_routes(app: Flask, adapters: dict) -> None:
    com = adapters["comment_adapter"]
    app.add_url_rule(
        "/articles/<int:article_id>/comments", view_func=com.create_comment, methods=["POST"], endpoint="comment.create_comment"
    )
    app.add_url_rule(
        "/articles/<int:article_id>/comments/<int:parent_comment_id>/reply",
        view_func=com.reply_to_comment,
        methods=["POST"],
        endpoint="comment.reply_to_comment",
    )
    app.add_url_rule(
        "/articles/<int:article_id>/comments/<int:comment_id>/delete",
        view_func=com.delete_comment,
        methods=["POST"],
        endpoint="comment.delete_comment",
    )


def _register_auth_routes(app: Flask, adapters: dict) -> None:
    log = adapters["login_adapter"]
    reg = adapters["registration_adapter"]
    acc = adapters["account_session_adapter"]
    app.add_url_rule("/login", view_func=log.render_login_page, methods=["GET"], endpoint="auth.login")
    app.add_url_rule("/login", view_func=log.authenticate, methods=["POST"], endpoint="auth.authenticate")
    app.add_url_rule("/register", view_func=reg.render_registration_page, methods=["GET"], endpoint="registration.register")
    app.add_url_rule("/register", view_func=reg.register, methods=["POST"], endpoint="registration.register_action")
    app.add_url_rule("/profile", view_func=acc.display_profile, endpoint="auth.profile")
    app.add_url_rule("/logout", view_func=acc.logout, methods=["POST"], endpoint="auth.logout")


def _register_file_routes(app: Flask, adapters: dict) -> None:
    fad = adapters["file_adapter"]
    csrf = app.extensions["csrf"]

    app.add_url_rule(
        "/api/upload/image",
        view_func=fad.upload_image,
        methods=["POST"],
        endpoint="file.upload_image",
    )
    csrf.exempt(fad.upload_image)

    app.add_url_rule(
        "/uploads/<string:file_id>/<string:filename>",
        view_func=fad.serve_file,
        methods=["GET"],
        endpoint="file.serve_file",
    )


def register_web_routes(app: Flask, adapters: dict) -> None:
    _register_article_routes(app, adapters)
    _register_article_api_routes(app, adapters)
    _register_comment_routes(app, adapters)
    _register_auth_routes(app, adapters)
    _register_file_routes(app, adapters)
