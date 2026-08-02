from flask import Flask
from flask_wtf.csrf import CSRFProtect

from flask_setup.middleware import _init_csrf_exemptions


class TestCsrfExempt:
    def test_exempt_returns_quietly_when_csrf_not_loaded(self):
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test_secret"
        app.config["TESTING"] = True
        _init_csrf_exemptions(app)

    def test_exempt_works_with_csrf_loaded(self):
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test_secret"
        app.config["TESTING"] = True
        CSRFProtect(app)
        _init_csrf_exemptions(app)
