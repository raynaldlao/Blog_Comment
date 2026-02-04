from flask import Flask

from app.configuration_variables import ConfigurationVariables
from app.controllers.auth import auth_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = ConfigurationVariables.SECRET_KEY
    app.register_blueprint(auth_bp)
    return app
