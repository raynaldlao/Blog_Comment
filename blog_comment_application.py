import os

from flask import Flask
from sqlalchemy.orm import Session

from config.database import setup_database
from config.env_config import env_config
from flask_setup.middleware import init_web_security
from flask_setup.routes import register_web_routes
from src.application.services.article_service import ArticleService
from src.application.services.comment_service import CommentService
from src.application.services.login_service import LoginService
from src.application.services.registration_service import RegistrationService
from src.infrastructure.input_adapters.flask.flask_account_session_adapter import AccountSessionAdapter
from src.infrastructure.input_adapters.flask.flask_article_adapter import ArticleAdapter
from src.infrastructure.input_adapters.flask.flask_comment_adapter import CommentAdapter
from src.infrastructure.input_adapters.flask.flask_login_adapter import LoginAdapter
from src.infrastructure.input_adapters.flask.flask_registration_adapter import RegistrationAdapter
from src.infrastructure.output_adapters.security.argon2_password_hasher_adapter import Argon2PasswordHasherAdapter
from src.infrastructure.output_adapters.session.flask_session_adapter import FlaskSessionAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter import SqlAlchemyAccountAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_article_adapter import SqlAlchemyArticleAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_comment_adapter import SqlAlchemyCommentAdapter
from utils.template_helpers import (
    date_format_filter,
    date_iso_filter,
    inject_current_year,
    nl2br_filter,
)


def _create_output_adapters(db_session: Session) -> dict:
    """
    Instantiates the persistence and security adapters.

    Args:
        db_session: The SQLAlchemy session to be injected into adapters.

    Returns:
        dict: A dictionary containing initialized output adapters.
    """
    account_repo = SqlAlchemyAccountAdapter(db_session)
    return {
        "account_repo": account_repo,
        "article_repo": SqlAlchemyArticleAdapter(db_session),
        "comment_repo": SqlAlchemyCommentAdapter(db_session),
        "session_repo": FlaskSessionAdapter(account_repo),
        "password_hasher_repository": Argon2PasswordHasherAdapter(
            time_cost=env_config.argon2_time_cost,
            memory_cost=env_config.argon2_memory_cost,
            parallelism=env_config.argon2_parallelism,
        ),
    }


def _create_services(repositories: dict) -> dict:
    """
    Instantiates the core application services.

    Args:
        repositories (dict): A dictionary of initialized repositories.

    Returns:
        dict: A dictionary containing initialized core services.
    """
    password_hasher_repository = repositories["password_hasher_repository"]
    registration_service = RegistrationService(repositories["account_repo"], password_hasher_repository)
    session_repo = repositories["session_repo"]
    account_repo = repositories["account_repo"]
    article_repo = repositories["article_repo"]
    comment_repo = repositories["comment_repo"]

    login_service = LoginService(account_repo, session_repo, password_hasher_repository)
    comment_service = CommentService(comment_repo, article_repo, account_repo)
    article_service = ArticleService(article_repo, account_repo, comment_repo)

    return {
        "registration_service": registration_service,
        "session_repo": session_repo,
        "login_service": login_service,
        "comment_service": comment_service,
        "article_service": article_service,
    }


def _init_web_adapters(services: dict) -> dict:
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
        "account_session_adapter": AccountSessionAdapter(services["login_service"]),
    }


def _init_web_facade_flask() -> Flask:
    """
    Initializes the Flask application instance (Web Facade).

    Returns:
        Flask: The initialized Flask application object.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "frontend/templates")
    static_dir = os.path.join(base_dir, "frontend/static")
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.secret_key = env_config.secret_key
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    return app


def _init_template_utils(app: Flask) -> None:
    """
    Registers custom Jinja2 filters and context processors on the Flask app.

    Provides the following filters to all templates:
        - ``nl2br``: Escapes HTML and converts newlines to ``<br>`` tags.
        - ``date_format``: Formats a ``datetime`` as a human-readable string.
        - ``date_iso``: Formats a ``datetime`` as an ISO 8601 date string.

    Injects the current UTC year into the template context as
    ``current_year`` via ``inject_current_year``.

    Args:
        app: The Flask application instance to configure.
    """
    app.jinja_env.filters["nl2br"] = nl2br_filter
    app.jinja_env.filters["date_format"] = date_format_filter
    app.jinja_env.filters["date_iso"] = date_iso_filter
    app.context_processor(inject_current_year)


def create_app(db_session=None) -> Flask:
    """
    Bootstrap function to initialize the hexagonal application.
    Orchestrates the assembly of the Core and the Web Facade.

    Args:
        db_session: Optional pre-existing database session.

    Returns:
        Flask: The configured Flask application (Web Facade).
    """
    db_session = setup_database(db_session)
    repositories = _create_output_adapters(db_session)
    services = _create_services(repositories)
    app = _init_web_facade_flask()
    init_web_security(app)
    _init_template_utils(app)
    web_adapters = _init_web_adapters(services)
    register_web_routes(app, web_adapters)
    web_adapters["account_session_adapter"].register_before_request_handler(app)
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
