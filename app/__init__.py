import os
import sys

from flask import Flask

from app.controllers.article import article_bp
from app.controllers.login import login_bp
from configurations.configuration_variables import env_vars


def initialize_flask_application():
    app = Flask(__name__)
    if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
        app.secret_key = env_vars.test_secret_key
    else:
        app.secret_key = env_vars.secret_key
    app.register_blueprint(login_bp)
    app.register_blueprint(article_bp)
    return app
