import os
from flask import Flask
from app.controllers.auth import auth_bp

def create_app():
    app = Flask(__name__)
    # This variable must be added to the .env file for it to work
    app.secret_key = os.getenv("SECRET_KEY")
    app.register_blueprint(auth_bp)
    return app