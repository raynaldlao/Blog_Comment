import os
import sys

from flask import Flask

from app.controllers.article_controller import article_bp
from app.controllers.comment_controller import comment_bp
from app.controllers.login_controller import login_bp
from config.configuration_variables import env_vars
from database.database_setup import db_session


def shutdown_session(exception: BaseException | None = None) -> None:
    """
    Removes the database session at the end of the request.

    Args:
        exception (BaseException | None): The exception that triggered the teardown, if any.
    """

    db_session.remove()


def initialize_flask_application() -> Flask:
    """
    Initializes and configures the Flask application.
    Sets the secret key based on the environment and registers blueprints.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
        app.secret_key = env_vars.test_secret_key
    else:
        app.secret_key = env_vars.secret_key

    app.register_blueprint(login_bp)
    app.register_blueprint(article_bp)
    app.register_blueprint(comment_bp)
    app.teardown_appcontext(shutdown_session)
    return app
