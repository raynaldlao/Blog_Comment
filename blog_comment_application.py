import base64
import hashlib
import os
from pathlib import Path

from flask import Flask, Response
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import Session

from config.database import setup_database
from config.env_config import env_config
from src.application.services.article_service import ArticleService
from src.application.services.comment_service import CommentService
from src.application.services.login_service import LoginService
from src.application.services.registration_service import RegistrationService
from src.infrastructure.input_adapters.flask.flask_account_session_adapter import AccountSessionAdapter
from src.infrastructure.input_adapters.flask.flask_article_adapter import ArticleAdapter
from src.infrastructure.input_adapters.flask.flask_comment_adapter import CommentAdapter
from src.infrastructure.input_adapters.flask.flask_login_adapter import LoginAdapter
from src.infrastructure.input_adapters.flask.flask_registration_adapter import RegistrationAdapter
from src.infrastructure.input_adapters.template_helpers import (
    date_format_filter,
    date_iso_filter,
    inject_current_year,
    nl2br_filter,
)
from src.infrastructure.output_adapters.security.argon2_password_hasher_adapter import Argon2PasswordHasherAdapter
from src.infrastructure.output_adapters.session.flask_session_adapter import FlaskSessionAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter import SqlAlchemyAccountAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_article_adapter import SqlAlchemyArticleAdapter
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_comment_adapter import SqlAlchemyCommentAdapter


class CSPConfig:
    """Configures Content Security Policy headers and violation reporting.

    Computes the SHA-256 hash of the inline theme script at startup,
    injects the Content-Security-Policy header into every response,
    and provides an endpoint for receiving CSP violation reports from
    the browser.
    """

    def __init__(self):
        self._script_hash = self._compute_inline_script_hash()

    @staticmethod
    def _compute_inline_script_hash() -> str:
        """Reads and hashes the inline theme script from base.html.

        Returns:
            str: The CSP-compatible hash string in ``'sha256-<base64>'`` format.
        """
        template_path = Path(__file__).parent / "src/infrastructure/input_adapters/templates/base.html"
        content = template_path.read_text()
        start = content.index("<script>") + len("<script>")
        end = content.index("</script>", start)
        digest = hashlib.sha256(content[start:end].encode()).digest()
        return "'sha256-" + base64.b64encode(digest).decode() + "'"

    def add_headers(self, response: Response) -> Response:
        """Injects the Content-Security-Policy and Reporting-Endpoints headers.

        Restricts resource loading to same-origin, Google Fonts, and the
        inline theme script (via SHA-256 hash). Configures CSP violation
        reporting via both report-uri (legacy) and report-to (modern).

        Args:
            response: The Flask response object to modify.

        Returns:
            Response: The modified Flask response with CSP and reporting
                headers set.
        """
        response.headers["Reporting-Endpoints"] = 'csp-endpoint="/csp-report"'
        response.headers["Content-Security-Policy"] = (
            "default-src 'self';"
            f"script-src 'self' {self._script_hash};"
            "style-src 'self' https://fonts.googleapis.com;"
            "font-src 'self' https://fonts.gstatic.com;"
            "img-src 'self' data:;"
            "base-uri 'self';"
            "form-action 'self';"
            "report-uri /csp-report;"
            "report-to csp-endpoint"
        )
        return response

    def handle_report(self) -> tuple[str, int]:
        """Logs incoming CSP violation reports and returns 204 No Content.

        Registered as a POST endpoint at /csp-report. The CSP report payload
        is read from Flask's request context (no explicit parameters).

        Returns:
            tuple: An empty response with HTTP 204 (No Content).
        """
        from flask import current_app, request
        current_app.logger.warning("CSP violation: %s", request.get_json())
        return "", 204


def _add_nosniff(response: Response) -> Response:
    """Sets the X-Content-Type-Options header to nosniff.

    Prevents the browser from MIME-type sniffing, forcing it to
    honour the declared Content-Type header. Mitigates MIME
    confusion attacks.

    Args:
        response: The Flask response object to modify.

    Returns:
        The modified Flask response with X-Content-Type-Options set.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


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


def _init_web_facade_flask() -> Flask:
    """
    Initializes the Flask application instance (Web Facade).

    Returns:
        Flask: The initialized Flask application object.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "src/infrastructure/input_adapters/templates")
    static_dir = os.path.join(base_dir, "src/infrastructure/input_adapters/static")
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.secret_key = env_config.secret_key
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    return app


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


def _register_article_routes(app: Flask, adapters: dict) -> None:
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
    app.add_url_rule("/logout", view_func=acc.logout, endpoint="auth.logout")


def _register_web_routes(app: Flask, adapters: dict) -> None:
    """
    Registers the URL rules for the Web interface facade.

    Args:
        app (Flask): The Flask application instance.
        adapters (dict): A dictionary of initialized Web adapters.
    """
    _register_article_routes(app, adapters)
    _register_comment_routes(app, adapters)
    _register_auth_routes(app, adapters)


def _init_web_security(app: Flask) -> None:
    """Configures web security middleware for the Flask application.

    Sets up CSRF protection, Content-Security-Policy headers with
    violation reporting, and the X-Content-Type-Options nosniff header.

    Args:
        app: The Flask application instance to secure.
    """
    csrf_protect = CSRFProtect(app)
    csp = CSPConfig()
    app.after_request(csp.add_headers)
    app.after_request(_add_nosniff)
    csrf_protect.exempt(csp.handle_report)
    app.add_url_rule("/csp-report", view_func=csp.handle_report, methods=["POST"])


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
    _init_web_security(app)
    app.jinja_env.filters["nl2br"] = nl2br_filter
    app.jinja_env.filters["date_format"] = date_format_filter
    app.jinja_env.filters["date_iso"] = date_iso_filter
    app.context_processor(inject_current_year)
    web_adapters = _init_web_adapters(services)
    _register_web_routes(app, web_adapters)
    web_adapters["account_session_adapter"].register_before_request_handler(app)
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
