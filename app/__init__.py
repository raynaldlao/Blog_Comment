from flask import Flask

from app.configuration_variables import ConfigurationVariables
from app.controllers.login import login_bp


def initialize_flask_application():
    app = Flask(__name__)
    app.secret_key = ConfigurationVariables.SECRET_KEY
    app.register_blueprint(login_bp)
    return app
