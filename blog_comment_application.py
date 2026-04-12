import os

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.services.account_session_service import AccountSessionService
from src.application.services.article_service import ArticleService
from src.application.services.comment_service import CommentService
from src.application.services.login_service import LoginService
from src.application.services.registration_service import RegistrationService
from src.infrastructure.config import infra_config
from src.infrastructure.input_adapters.flask.flask_account_session_adapter import AccountSessionAdapter
from src.infrastructure.input_adapters.flask.flask_article_adapter import ArticleAdapter
from src.infrastructure.input_adapters.flask.flask_comment_adapter import CommentAdapter
from src.infrastructure.input_adapters.flask.flask_handler import FlaskHandler
from src.infrastructure.input_adapters.flask.flask_login_adapter import LoginAdapter
from src.infrastructure.input_adapters.flask.flask_registration_adapter import RegistrationAdapter
from src.infrastructure.output_adapters.session.flask_session_adapter import FlaskSessionAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter import SqlAlchemyAccountAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_article_adapter import SqlAlchemyArticleAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_comment_adapter import SqlAlchemyCommentAdapter


def create_app() -> Flask:
    """
    Bootstrap function to initialize the hexagonal application.
    Handles dependency injection and manual route registration.

    Returns:
        Flask: The configured Flask application.
    """
    # 1. Database Setup
    engine = create_engine(infra_config.database_url)
    session_factory = sessionmaker(bind=engine)
    db_session = session_factory()

    # 2. Output Adapters (Repositories)
    account_repo = SqlAlchemyAccountAdapter(db_session)
    article_repo = SqlAlchemyArticleAdapter(db_session)
    comment_repo = SqlAlchemyCommentAdapter(db_session)

    # 3. Core Application (Services)
    registration_service = RegistrationService(account_repo)
    session_repo = FlaskSessionAdapter()
    session_service = AccountSessionService(session_repo, account_repo)
    login_service = LoginService(account_repo, session_service)
    comment_service = CommentService(comment_repo, article_repo, account_repo)
    article_service = ArticleService(article_repo, account_repo, comment_service)

    # 4. Input Adapters (Flask)
    template_dir = os.path.abspath("src/infrastructure/input_adapters/templates")
    static_dir = os.path.abspath("src/infrastructure/input_adapters/static")
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")

    article_adapter = ArticleAdapter(article_service)
    comment_adapter = CommentAdapter(comment_service)
    login_adapter = LoginAdapter(login_service)
    registration_adapter = RegistrationAdapter(registration_service)
    account_session_adapter = AccountSessionAdapter(session_service)

    # 5. Manual Route Registration (No Blueprints)
    # Article Routes (Namespace simulation: article.xxx)
    app.add_url_rule("/", view_func=article_adapter.list_articles, endpoint="article.list_articles")
    app.add_url_rule("/articles/<int:article_id>", view_func=article_adapter.read_article, endpoint="article.read_article")
    app.add_url_rule("/articles/new", view_func=article_adapter.render_create_page, methods=["GET"], endpoint="article.render_create_page")
    app.add_url_rule("/articles/new", view_func=article_adapter.create_article, methods=["POST"], endpoint="article.create_article")
    app.add_url_rule("/articles/<int:article_id>/edit", view_func=article_adapter.render_edit_page, methods=["GET"], endpoint="article.render_edit_page")
    app.add_url_rule("/articles/<int:article_id>/edit", view_func=article_adapter.update_article, methods=["POST"], endpoint="article.update_article")
    app.add_url_rule("/articles/<int:article_id>/delete", view_func=article_adapter.delete_article, methods=["POST"], endpoint="article.delete_article")

    # Comment Routes (Namespace simulation: comment.xxx)
    app.add_url_rule("/articles/<int:article_id>/comments", view_func=comment_adapter.create_comment, methods=["POST"], endpoint="comment.create_comment")
    app.add_url_rule("/articles/<int:article_id>/comments/<int:parent_comment_id>/reply", view_func=comment_adapter.reply_to_comment, methods=["POST"], endpoint="comment.reply_to_comment")
    app.add_url_rule("/articles/<int:article_id>/comments/<int:comment_id>/delete", view_func=comment_adapter.delete_comment, methods=["POST"], endpoint="comment.delete_comment")

    # Auth & Registration Routes (Simulating namespaces)
    app.add_url_rule("/login", view_func=login_adapter.render_login_page, methods=["GET"], endpoint="auth.login")
    app.add_url_rule("/login", view_func=login_adapter.authenticate, methods=["POST"], endpoint="auth.authenticate")
    app.add_url_rule("/register", view_func=registration_adapter.render_registration_page, methods=["GET"], endpoint="registration.register")
    app.add_url_rule("/register", view_func=registration_adapter.register, methods=["POST"], endpoint="registration.register_action")
    app.add_url_rule("/profile", view_func=account_session_adapter.display_profile, endpoint="auth.profile")
    app.add_url_rule("/logout", view_func=account_session_adapter.logout, endpoint="auth.logout")

    # 6. Global Handlers (Identity Concierge)
    FlaskHandler.register_before_request_handler(app, session_service)

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
