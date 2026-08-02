import glob
import os
from datetime import timedelta
from typing import NamedTuple

from flask import Flask, flash, redirect, render_template, session, url_for
from flask_babel import Babel
from flask_babel import gettext as _
from flask_compress import Compress
from sqlalchemy.orm import Session

from config.env_config import env_config
from flask_setup.middleware import _init_csrf_exemptions, init_rate_limiter, init_web_security
from flask_setup.routes import register_web_routes
from flask_setup.template_helpers import (
    ViteManifest,
    date_iso_filter,
    format_datetime_locale,
    inject_current_user,
    inject_current_year,
    inject_vite_assets,
)
from src.application.services.admin_service import AdminService
from src.application.services.article_service import ArticleService
from src.application.services.comment_service import CommentService
from src.application.services.file_service import FileService
from src.application.services.login_service import LoginService
from src.application.services.registration_service import RegistrationService
from src.infrastructure.input_adapters.flask.flask_account_session_adapter import AccountSessionAdapter
from src.infrastructure.input_adapters.flask.flask_admin_adapter import AdminAdapter
from src.infrastructure.input_adapters.flask.flask_article_adapter import ArticleAdapter
from src.infrastructure.input_adapters.flask.flask_comment_adapter import CommentAdapter
from src.infrastructure.input_adapters.flask.flask_file_adapter import FlaskFileAdapter
from src.infrastructure.input_adapters.flask.flask_login_adapter import LoginAdapter
from src.infrastructure.input_adapters.flask.flask_registration_adapter import RegistrationAdapter
from src.infrastructure.output_adapters.security.argon2_password_hasher_adapter import Argon2PasswordHasherAdapter
from src.infrastructure.output_adapters.session.flask_session_adapter import FlaskSessionAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter import SqlAlchemyAccountAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_article_adapter import SqlAlchemyArticleAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_comment_adapter import SqlAlchemyCommentAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_file_storage_adapter import SqlAlchemyFileStorageAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_setup_database import setup_database
from utils.prosemirror_to_html import prosemirror_to_html


class Repositories(NamedTuple):
    """Typed container for persistence and security output adapters."""

    account_repo: SqlAlchemyAccountAdapter
    article_repo: SqlAlchemyArticleAdapter
    comment_repo: SqlAlchemyCommentAdapter
    file_storage_repo: SqlAlchemyFileStorageAdapter
    session_repo: FlaskSessionAdapter
    password_hasher_repository: Argon2PasswordHasherAdapter


class Services(NamedTuple):
    """Typed container for core application services."""

    registration_service: RegistrationService
    session_repo: FlaskSessionAdapter
    login_service: LoginService
    comment_service: CommentService
    article_service: ArticleService
    file_service: FileService
    admin_service: AdminService


class WebAdapters(NamedTuple):
    """Typed container for Flask input adapters."""

    article_adapter: ArticleAdapter
    comment_adapter: CommentAdapter
    login_adapter: LoginAdapter
    registration_adapter: RegistrationAdapter
    account_session_adapter: AccountSessionAdapter
    admin_adapter: AdminAdapter
    file_adapter: FlaskFileAdapter


def _get_argon2_params(db_session: Session | None = None) -> tuple[int, int, int]:
    """
    Selects Argon2 parameters based on environment.

    Uses test (low-security) parameters when a test session is provided,
    production (high-security) parameters otherwise.

    Args:
        db_session: SQLAlchemy session. If ``None``, returns production params.

    Returns:
        tuple[int, int, int]: (time_cost, memory_cost, parallelism).
    """
    if db_session is not None:
        return (
            env_config.test_argon2_time_cost,
            env_config.test_argon2_memory_cost,
            env_config.test_argon2_parallelism,
        )
    return (
        env_config.argon2_time_cost,
        env_config.argon2_memory_cost,
        env_config.argon2_parallelism,
    )


def _create_output_adapters(db_session: Session) -> Repositories:
    """
    Instantiates persistence and security adapters.

    Uses test argon2 parameters when db_session is provided (test mode),
    production argon2 parameters otherwise.

    Args:
        db_session: SQLAlchemy session for dependency injection.

    Returns:
        Repositories: Typed container of initialized output adapters.
    """
    time_cost, memory_cost, parallelism = _get_argon2_params(db_session)
    account_repo = SqlAlchemyAccountAdapter(db_session)
    return Repositories(
        account_repo=account_repo,
        article_repo=SqlAlchemyArticleAdapter(db_session),
        comment_repo=SqlAlchemyCommentAdapter(db_session),
        file_storage_repo=SqlAlchemyFileStorageAdapter(db_session),
        session_repo=FlaskSessionAdapter(account_repo),
        password_hasher_repository=Argon2PasswordHasherAdapter(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
        ),
    )


def _create_services(repositories: Repositories) -> Services:
    """
    Instantiates the core application services.

    Args:
        repositories: Container of initialized output adapters.

    Returns:
        Services: Typed container of initialized core services.
    """
    password_hasher_repository = repositories.password_hasher_repository
    registration_service = RegistrationService(repositories.account_repo, password_hasher_repository)
    session_repo = repositories.session_repo
    account_repo = repositories.account_repo
    article_repo = repositories.article_repo
    comment_repo = repositories.comment_repo

    file_service = FileService(repositories.file_storage_repo)
    comment_service = CommentService(comment_repo, article_repo, account_repo)
    login_service = LoginService(
        account_repo, session_repo, password_hasher_repository,
        file_service=file_service,
        comment_service=comment_service,
    )
    article_service = ArticleService(article_repo, account_repo, comment_repo, file_service=file_service)
    admin_service = AdminService(
        account_repo,
        file_service=file_service,
        comment_service=comment_service,
    )

    return Services(
        registration_service=registration_service,
        session_repo=session_repo,
        login_service=login_service,
        comment_service=comment_service,
        article_service=article_service,
        file_service=file_service,
        admin_service=admin_service,
    )


def _init_web_adapters(services: Services) -> WebAdapters:
    """
    Instantiates the input adapters for the Web interface.

    Args:
        services: Container of initialized core services.

    Returns:
        WebAdapters: Typed container of initialized Flask adapters.
    """
    return WebAdapters(
        article_adapter=ArticleAdapter(services.article_service),
        comment_adapter=CommentAdapter(services.comment_service),
        login_adapter=LoginAdapter(services.login_service),
        registration_adapter=RegistrationAdapter(services.registration_service),
        account_session_adapter=AccountSessionAdapter(
            services.login_service,
        ),
        admin_adapter=AdminAdapter(services.admin_service),
        file_adapter=FlaskFileAdapter(services.file_service),
    )


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
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
    return app


def _init_template_utils(app: Flask) -> None:
    """
    Registers custom Jinja2 filters and context processors on the Flask app.

    Provides the following filters to all templates:
        - ``date_format``: Formats a ``datetime`` as a human-readable string.
        - ``date_iso``: Formats a ``datetime`` as an ISO 8601 date string.

    Injects the current UTC year into the template context as
    ``current_year`` via ``inject_current_year``.

    Injects Vite asset URLs (``vite_js_url``, ``vite_css_urls``) for the
    BlockNote React frontend build.

    Args:
        app: The Flask application instance to configure.
    """
    ViteManifest.init(os.path.join(app.static_folder or "", "dist"))

    app.jinja_env.filters["date_iso"] = date_iso_filter
    app.jinja_env.filters["prosemirror_to_html"] = prosemirror_to_html
    app.jinja_env.filters["format_datetime_locale"] = format_datetime_locale
    app.context_processor(inject_current_year)
    app.context_processor(inject_vite_assets)
    app.context_processor(inject_current_user)


def _error_page(code: int, message: str) -> tuple[str, int]:
    """Render generic error page with given HTTP status code and message."""
    return render_template("error.html", code=code, message=message), code


def _on_rate_breach(_request_limit: object) -> None:
    """Flash a warning when IP-based rate limit is exceeded.

    Called by flask-limiter before aborting with 429.
    The flash appears on the redirected login page.

    Args:
        _request_limit: The RequestLimit object from flask-limiter (unused).
    """
    flash(
        _("Too many login attempts. Please try again later."),
        "error",
    )


def _shutdown_db_session(exception: BaseException | None = None) -> None:
    """Remove the scoped DB session at the end of each request.

    Uses ``current_app.config.get()`` (not ``pop``) to avoid removing
    the shared key from ``app.config`` after the first request. Must
    remain callable for all subsequent requests.

    Reads the session from the Flask app config and removes it
    from the current thread registry. Idempotent — safe to call
    multiple times.

    Args:
        exception: The exception that occurred during the request,
            or None if the request completed successfully.
    """
    from flask import current_app
    session = current_app.config.get("_DB_SESSION")
    if session is not None:
        session.remove()


def _inject_get_locale() -> dict:
    """Inject the current locale into all templates.

    Returns a single-entry dictionary so templates can call
    ``get_locale()`` to retrieve the active locale string
    from the session.

    Returns:
        dict: A dictionary with key ``"get_locale"`` whose value
        is a callable returning the locale string.
    """
    return {"get_locale": lambda: session.get("lang", "fr")}

def create_app(db_session: Session | None = None, testing: bool = False) -> Flask:
    """
    Bootstrap function to initialize the hexagonal application.

    Orchestrates the assembly of the Core and the Web Facade.

    Creates a scoped SQLAlchemy session (thread-safe, one per thread)
    and registers a teardown handler that removes the session from the
    current thread at the end of each request.

    When a test session is injected via ``db_session``, the caller
    owns the session lifecycle and no teardown handler is registered
    (the test fixture handles cleanup via its own ``session.remove()``).

    Args:
        db_session: Optional pre-existing database session.
        testing: Disables rate limit enforcement when ``True``
            (used in tests). The wrapper is always present but
            flask-limiter is inactive, avoiding test interference.

    Returns:
        Flask: The configured Flask application (Web Facade).
    """
    _injected_session = db_session is not None
    db_session = setup_database(db_session)
    repositories = _create_output_adapters(db_session)
    services = _create_services(repositories)
    app = _init_web_facade_flask()

    if not _injected_session and hasattr(db_session, "remove"):
        app.config["_DB_SESSION"] = db_session
        app.teardown_appcontext(_shutdown_db_session)

    Compress(app)
    Babel(app, locale_selector=lambda: session.get("lang", "fr"))
    app.context_processor(_inject_get_locale)
    init_web_security(app)
    _init_template_utils(app)
    web_adapters = _init_web_adapters(services)
    register_web_routes(app, web_adapters)
    _init_csrf_exemptions(app)
    web_adapters.account_session_adapter.register_before_request_handler(app)
    limiter = init_rate_limiter(app, enabled=not testing)
    app.extensions.setdefault("limiter", set()).add(limiter)

    original_login = app.view_functions["auth.authenticate"]

    @limiter.limit("5/minute", on_breach=_on_rate_breach)
    def rate_limited_login(*args: object, **kwargs: object):
        """Wrap login endpoint with IP-based rate limiting.

        Limits POST /login to 5 requests per minute per IP.
        On breach, ``_on_rate_breach`` flashes a warning,
        then flask-limiter aborts with 429 which triggers
        the login redirect.

        Args:
            *args: Forwarded to original login view.
            **kwargs: Forwarded to original login view.

        Returns:
            Response from the original login view.
        """
        return original_login(*args, **kwargs)

    app.view_functions["auth.authenticate"] = rate_limited_login  # type: ignore[assignment]

    app.errorhandler(429)(
        lambda e: redirect(url_for("auth.login"))
    )

    app.errorhandler(403)(lambda e: _error_page(403, _("You do not have permission to access this page.")))
    app.errorhandler(404)(lambda e: _error_page(404, _("The page you are looking for does not exist.")))
    app.errorhandler(500)(lambda e: _error_page(500, _("An unexpected error occurred. Please try again later.")))
    return app


if __name__ == "__main__":  # pragma: no cover
    application = create_app()
    application.run(
        debug=env_config.flask_debug,
        extra_files=glob.glob("translations/**/*.mo", recursive=True),
    )
