"""Authentication decorators for Flask adapters.

Provides @require_auth (HTML redirect) and @require_auth_api (401 JSON)
to replace duplicated user-check boilerplate across adapters.
"""

from functools import wraps

from flask import flash, jsonify, redirect, url_for
from flask import g as global_request_context
from flask_babel import gettext as _


def require_auth(flash_message="You must be signed in.", redirect_to="auth.login"):
    """Decorator factory that requires an authenticated user.

    If the user is not authenticated, flashes the given message and
    redirects to the specified endpoint. The decorated method can
    retrieve the user via ``global_request_context.get("current_user")``
    which is guaranteed non-None after this decorator passes.

    Args:
        flash_message: Message flashed on authentication failure.
        redirect_to: Flask endpoint name to redirect to.

    Returns:
        Callable: Decorator that wraps the view function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = global_request_context.get("current_user")
            if not user:
                flash(_(flash_message), "error")
                return redirect(url_for(redirect_to))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_auth_api():
    """Decorator that requires an authenticated user for JSON API endpoints.

    Returns a 401 JSON response if the user is not authenticated.
    The decorated method can retrieve the user via
    ``global_request_context.get("current_user")`` which is guaranteed
    non-None after this decorator passes.

    Returns:
        Callable: Decorator that wraps the view function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = global_request_context.get("current_user")
            if not user:
                return jsonify({"error": _("Unauthorized.")}), 401
            return func(*args, **kwargs)

        return wrapper

    return decorator
