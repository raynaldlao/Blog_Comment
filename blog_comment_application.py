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


def _setup_database(db_session=None):
    """
    Initializes the database connection and session.

    Args:
        db_session: Optional existing SQLAlchemy session (e.g., for testing).

    Returns:
        Session: A configured SQLAlchemy database session.
    """
    if db_session is None:
        engine = create_engine(infra_config.database_url)
        session_factory = sessionmaker(bind=engine)
        db_session = session_factory()
    return db_session


def _create_output_adapters(db_session):
    """
    Instantiates the persistence adapters (repositories).

    Args:
        db_session: The SQLAlchemy session to be injected into adapters.

    Returns:
        dict: A dictionary containing initialized repository adapters.
    """
    return {
        "account_repo": SqlAlchemyAccountAdapter(db_session),
        "article_repo": SqlAlchemyArticleAdapter(db_session),
        "comment_repo": SqlAlchemyCommentAdapter(db_session),
        "session_repo": FlaskSessionAdapter(),
    }


def _create_services(repositories):
    """
    Instantiates the core application services.

    Args:
        repositories (dict): A dictionary of initialized repositories.

    Returns:
        dict: A dictionary containing initialized core services.
    """
    registration_service = RegistrationService(repositories["account_repo"])
    session_repo = repositories["session_repo"]
    account_repo = repositories["account_repo"]
    article_repo = repositories["article_repo"]
    comment_repo = repositories["comment_repo"]

    session_service = AccountSessionService(session_repo, account_repo)
    login_service = LoginService(account_repo, session_service)
    comment_service = CommentService(comment_repo, article_repo, account_repo)
    article_service = ArticleService(article_repo, account_repo, comment_repo)

    return {
        "registration_service": registration_service,
        "session_service": session_service,
        "login_service": login_service,
        "comment_service": comment_service,
        "article_service": article_service,
    }


def _init_web_facade_flask():
    """
    Initializes the Flask application instance (Web Facade).

    Returns:
        Flask: The initialized Flask application object.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "src/infrastructure/input_adapters/templates")
    static_dir = os.path.join(base_dir, "src/infrastructure/input_adapters/static")
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")
    return app


def _init_web_adapters(services):
    """
    Instantiates the input adapters for the Web interface.

    Args:
        services (dict): A dictionary of initialized core services.

    Returns:
        dict: A dictionary containing initialized Flask adapters.
    """
    return {
        "article_adapter": ArticleAdapter(services["article_service"]),
        "comment_adapter": CommentAdapter(services["comment_service"]),
        "login_adapter": LoginAdapter(services["login_service"]),
        "registration_adapter": RegistrationAdapter(services["registration_service"]),
        "account_session_adapter": AccountSessionAdapter(services["session_service"]),
    }


def _register_web_routes(app, adapters):
    """
    Registers the URL rules for the Web interface facade.

    Args:
        app (Flask): The Flask application instance.
        adapters (dict): A dictionary of initialized Web adapters.
    """
    art = adapters["article_adapter"]
    app.add_url_rule("/", view_func=art.list_articles, endpoint="article.list_articles")
    app.add_url_rule("/articles/<int:article_id>", view_func=art.read_article, endpoint="article.read_article")
    app.add_url_rule("/articles/new", view_func=art.render_create_page, methods=["GET"], endpoint="article.render_create_page")
    app.add_url_rule("/articles/new", view_func=art.create_article, methods=["POST"], endpoint="article.create_article")
    app.add_url_rule(
        "/articles/<int:article_id>/edit", view_func=art.render_edit_page, methods=["GET"], endpoint="article.render_edit_page"
    )
    app.add_url_rule(
        "/articles/<int:article_id>/edit", view_func=art.update_article, methods=["POST"], endpoint="article.update_article"
    )
    app.add_url_rule(
        "/articles/<int:article_id>/delete", view_func=art.delete_article, methods=["POST"], endpoint="article.delete_article"
    )

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

    log = adapters["login_adapter"]
    reg = adapters["registration_adapter"]
    acc = adapters["account_session_adapter"]
    app.add_url_rule("/login", view_func=log.render_login_page, methods=["GET"], endpoint="auth.login")
    app.add_url_rule("/login", view_func=log.authenticate, methods=["POST"], endpoint="auth.authenticate")
    app.add_url_rule("/register", view_func=reg.render_registration_page, methods=["GET"], endpoint="registration.register")
    app.add_url_rule("/register", view_func=reg.register, methods=["POST"], endpoint="registration.register_action")
    app.add_url_rule("/profile", view_func=acc.display_profile, endpoint="auth.profile")
    app.add_url_rule("/logout", view_func=acc.logout, endpoint="auth.logout")


def create_app(db_session=None) -> Flask:
    """
    Bootstrap function to initialize the hexagonal application.
    Orchestrates the assembly of the Core and the Web Facade.

    Args:
        db_session: Optional pre-existing database session.

    Returns:
        Flask: The configured Flask application (Web Facade).
    """
    db_session = _setup_database(db_session)
    repositories = _create_output_adapters(db_session)
    services = _create_services(repositories)
    app = _init_web_facade_flask()
    web_adapters = _init_web_adapters(services)
    _register_web_routes(app, web_adapters)
    FlaskHandler.register_before_request_handler(app, services["session_service"])
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
