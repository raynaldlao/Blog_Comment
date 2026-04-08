import os

from flask import Flask, get_flashed_messages


class FlaskInputAdapterTestBase:
    """
    Shared base class for Flask input adapter tests.
    Centralizes Flask application setup, template path resolution,
    and common test configuration to eliminate duplication.
    """

    TEMPLATE_DIR = os.path.abspath("src/infrastructure/input_adapters/templates")

    def setup_method(self):
        """
        Sets up the Flask test client and pushes the application context globally.
        Child test classes can simply use `self.client` without context managers.
        """
        self.app = Flask(__name__, template_folder=self.TEMPLATE_DIR)
        self.app.config["SECRET_KEY"] = "test_secret"
        self.app.config["SERVER_NAME"] = "localhost"
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.app_context = self.app.test_request_context()
        self.app_context.push()

    def teardown_method(self):
        """Pops the application context after each test."""
        self.app_context.pop()

    def _register_dummy_route(self, rule, endpoint, label=None):
        """
        Registers a dummy route that returns flashed messages.
        Useful for testing redirects to routes owned by other adapters.

        Args:
            rule (str): The URL rule (e.g. "/articles").
            endpoint (str): The Flask endpoint name (e.g. "article.list_articles").
            label (str): Optional label included in the response body.
        """
        if label is None:
            label = endpoint

        def dummy_view():
            return f"{label} {get_flashed_messages()}"

        self.app.add_url_rule(rule, view_func=dummy_view, endpoint=endpoint)
