import os

from flask import Flask, get_flashed_messages, request
from flask import g as global_request_context
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect

from utils.prosemirror_to_html import prosemirror_to_html
from utils.template_helpers import date_format_filter, date_iso_filter, format_datetime_locale, nl2br_filter


class FlaskInputAdapterTestBase:
    """
    Shared base class for Flask input adapter tests.
    Centralizes Flask application setup, template path resolution,
    and common test configuration to eliminate duplication.
    """

    TEMPLATE_DIR = os.path.abspath("frontend/templates")

    def _inject_test_user_hook(self) -> None:
        """
        Hook registered on the app to inject a domain Account into the global request context.
        """
        if self._test_user:
            global_request_context.current_user = self._test_user

    def _dummy_view_handler(self, **kwargs) -> str:
        """
        Generic view handler for dummy routes.
        Uses the request endpoint to retrieve the appropriate label.

        Returns:
            str: The response body containing the label and flashed messages.
        """
        label = self._dummy_labels.get(request.endpoint, request.endpoint)
        messages = get_flashed_messages(with_categories=True)
        html = f"<html><body><p>{label}</p>"
        for category, message in messages:
            html += f'<div class="alert alert-{category}">{message}</div>'
        html += "</body></html>"
        return html

    def _register_dummy_route(self, rule, endpoint, label=None) -> None:
        """
        Registers a dummy route using a class-level handler.

        Args:
            rule (str): The URL rule (e.g. "/articles").
            endpoint (str): The Flask endpoint name.
            label (str): Optional label returned in the response.
        """
        self._dummy_labels[endpoint] = label or endpoint
        self.app.add_url_rule(rule, view_func=self._dummy_view_handler, endpoint=endpoint)

    def setup_method(self) -> None:
        """
        Sets up the Flask test client and pushes the application context globally.
        Initializes test state and registers class-level hooks to avoid nested functions.
        """
        frontend_dir = os.path.dirname(self.TEMPLATE_DIR)
        static_dir = os.path.join(frontend_dir, "static")
        self.app = Flask(__name__, template_folder=self.TEMPLATE_DIR, static_folder=static_dir)

        self.app.jinja_env.filters["nl2br"] = nl2br_filter
        self.app.jinja_env.filters["date_format"] = date_format_filter
        self.app.jinja_env.filters["date_iso"] = date_iso_filter
        self.app.jinja_env.filters["prosemirror_to_html"] = prosemirror_to_html
        self.app.jinja_env.filters["format_datetime_locale"] = format_datetime_locale
        self.app.config["SECRET_KEY"] = "test_secret"
        self.app.config["SERVER_NAME"] = "localhost"
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        Babel(self.app)
        self.app.extensions["babel"].locale_selector = lambda: "en"
        CSRFProtect(self.app)
        self._test_user = None
        self._dummy_labels = {}
        self.app.before_request(self._inject_test_user_hook)
        self.client = self.app.test_client()
        self.app_context = self.app.test_request_context()
        self.app_context.push()

    def teardown_method(self) -> None:
        """Pops the application context after each test."""
        self.app_context.pop()

    def set_current_user(self, account) -> None:
        """
        Affects a domain Account as the current test user.

        Args:
            account (Account): The domain entity to inject.
        """
        self._test_user = account
