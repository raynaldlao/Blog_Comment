from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import flash, redirect, session, url_for

from app.constants import Role, SessionKey


def login_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure that a user is logged in before accessing a route.

    Args:
        f (Callable): The route function to wrap.

    Returns:
        Callable: The wrapped function.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not session.get(SessionKey.USER_ID):
            flash("Login required.")
            return redirect(url_for("login.render_login_page"))
        return f(*args, **kwargs)

    return decorated_function


def roles_accepted(*roles: Role) -> Callable[..., Any]:
    """
    Decorator to ensure that a logged-in user has one of the required roles.

    Args:
        *roles (Role): Variable list of accepted roles.

    Returns:
        Callable: A decorator that wraps the route function.
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        @login_required
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            user_role = session.get(SessionKey.ROLE)
            if user_role not in [role.value for role in roles]:
                flash("Access restricted: Insufficient permissions.")
                return redirect(url_for("article.list_articles"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator
