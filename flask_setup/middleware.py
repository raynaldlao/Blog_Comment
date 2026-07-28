import base64
import hashlib
from pathlib import Path

from flask import Flask, Response
from flask import request as flask_request
from flask.sessions import SecureCookieSessionInterface
from flask_wtf.csrf import CSRFProtect


class CSPConfig:
    """Configures Content Security Policy headers and violation reporting.

    Computes the SHA-256 hash of the inline theme script from base.html
    in the given template directory at startup, injects the
    Content-Security-Policy header into every response, and provides
    an endpoint for receiving CSP violation reports from the browser.
    """

    def __init__(self, template_dir: str | Path):
        """
        Initializes CSP configuration and computes the inline script hash.

        Args:
            template_dir: Path to the directory containing base.html
                with the inline theme script. Typically derived from
                app.root_path.
        """
        self._template_dir = Path(template_dir)
        self._script_hash = self._compute_inline_script_hash()

    def _compute_inline_script_hash(self) -> str:
        """Reads and hashes the inline theme script from base.html.

        Resolves base.html relative to the template_dir passed at init,
        avoiding fragile __file__-based paths.

        Returns:
            str: The CSP-compatible hash string in ``'sha256-<base64>'`` format.
        """
        template_path = self._template_dir / "base.html"
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
            f"script-src 'self' 'unsafe-eval' 'unsafe-hashes' 'sha256-MhtPZXr7+LpJUY5qtMutB+qWfQtMaPccfe7QXtCcEYc=' {self._script_hash};"
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;"
            "font-src 'self' https://fonts.gstatic.com;"
            "img-src 'self' data: https:;"
            "frame-src https://www.youtube.com;"
            "connect-src 'self' https://cdn.jsdelivr.net;"
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


def _add_x_frame_options(response: Response) -> Response:
    """Sets the X-Frame-Options header to DENY.

    Prevents the site from being embedded in third-party iframes,
    mitigating clickjacking attacks.

    Args:
        response: The Flask response object to modify.

    Returns:
        The modified Flask response with X-Frame-Options set.
    """
    response.headers["X-Frame-Options"] = "DENY"
    return response


def _add_referrer_policy(response: Response) -> Response:
    """Sets the Referrer-Policy header to strict-origin-when-cross-origin.

    Prevents the full URL from leaking to external sites. Only the
    origin is sent for cross-origin HTTPS requests, and nothing is
    sent when downgrading from HTTPS to HTTP.

    Args:
        response: The Flask response object to modify.

    Returns:
        The modified Flask response with Referrer-Policy set.
    """
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


def _add_cache_headers(response: Response) -> Response:
    """Sets Cache-Control headers based on request path.

    Fingerprinted Vite dist assets (static/dist/) get long-term immutable
    cache. Non-fingerprinted static files (CSS, JS, fonts) get no-cache
    to force revalidation. Uploaded files have UUID-based URLs so they
    are also cached indefinitely. All other routes (HTML pages) get
    no-store to prevent the browser from caching sensitive pages.

    Args:
        response: The Flask response object to modify.

    Returns:
        The modified Flask response with Cache-Control set for
        matching paths.
    """
    if flask_request:
        path = flask_request.path
        if path.startswith("/static/"):
            if path.startswith("/static/dist/"):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                response.headers["Cache-Control"] = "no-cache"
        elif path.startswith("/uploads/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
    return response


class NonPersistentSessionInterface(SecureCookieSessionInterface):
    """Session interface that removes the cookie Expires header.

    The cookie is treated as a browser-session cookie (deleted on browser close)
    while keeping the server-side timeout via PERMANENT_SESSION_LIFETIME.
    """

    def get_expiration_time(self, app, session):
        return None


def _init_csrf_exemptions(app: Flask) -> None:
    """Applies CSRF exemptions to API and internal endpoints.

    Must be called AFTER all routes are registered so that
    ``app.view_functions`` can resolve endpoint names to view
    functions. Exemptions are defined here (not in routes.py)
    to keep a single source of truth for endpoints that skip
    CSRF protection.

    Args:
        app: The Flask application instance with all routes
            already registered.
    """
    endpoints = [
        "article.api_get",
        "article.api_create",
        "article.api_update",
        "article.api_delete",
        "auth.upload_profile_photo",
        "file.upload_image",
        "csp.handle_report",
    ]
    csrf = app.extensions.get("csrf")
    if not csrf:
        return
    for endpoint in endpoints:
        view_func = app.view_functions.get(endpoint)
        if view_func:
            csrf.exempt(view_func)


def init_web_security(app: Flask) -> None:
    """Configures web security middleware for the Flask application.

    Sets up CSRF protection, Content-Security-Policy headers with
    violation reporting, and the X-Content-Type-Options nosniff header.

    Args:
        app: The Flask application instance to secure.
    """
    app.session_interface = NonPersistentSessionInterface()
    app.config["WTF_CSRF_TIME_LIMIT"] = None
    CSRFProtect(app)
    template_dir = Path(app.root_path) / "frontend" / "templates"
    csp = CSPConfig(template_dir)
    app.after_request(csp.add_headers)
    app.after_request(_add_nosniff)
    app.after_request(_add_x_frame_options)
    app.after_request(_add_referrer_policy)
    app.after_request(_add_cache_headers)
    app.add_url_rule(
        "/csp-report", view_func=csp.handle_report,
        methods=["POST"], endpoint="csp.handle_report",
    )
