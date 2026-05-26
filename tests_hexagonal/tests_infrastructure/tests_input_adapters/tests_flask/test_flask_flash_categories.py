"""Tests for flash message category rendering in templates."""

from flask import flash, render_template

from tests_hexagonal.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class TestFlashCategories(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.app.config["SECRET_KEY"] = "test_secret"
        self.app.config["SERVER_NAME"] = "localhost"
        self.app.config["TESTING"] = True
        self._register_dummy_route("/login", "auth.login", "auth")
        self._register_dummy_route("/", "article.list_articles", "home")
        self._register_dummy_route("/profile", "auth.profile", "profile")
        self._register_dummy_route("/logout", "auth.logout", "logout")
        self._register_dummy_route("/register", "registration.register", "reg")

    def _register_flash_route(self, category, message):
        def view():
            flash(message, category)
            return render_template("base.html")

        self.app.add_url_rule(f"/{category}", view_func=view, endpoint=f"flash_{category}")

    def test_success_flash_renders_alert_success(self):
        self._register_flash_route("success", "Operation succeeded")
        response = self.client.get("/success")
        assert b"Operation succeeded" in response.data
        assert b"alert-success" in response.data

    def test_error_flash_renders_alert_error(self):
        self._register_flash_route("error", "Something went wrong")
        response = self.client.get("/error")
        assert b"Something went wrong" in response.data
        assert b"alert-error" in response.data

    def test_info_flash_renders_alert_info(self):
        self._register_flash_route("info", "Here is some info")
        response = self.client.get("/info")
        assert b"Here is some info" in response.data
        assert b"alert-info" in response.data
