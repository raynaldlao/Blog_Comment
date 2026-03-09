import sys
from unittest.mock import patch

from app import initialize_flask_application


def test_initialize_app_production_secret_key():
    with patch("os.getenv") as mock_getenv, \
         patch.dict(sys.modules, {}):
        if "pytest" in sys.modules:
            del sys.modules["pytest"]

        mock_getenv.return_value = None
        with patch("app.env_vars") as mock_env_vars:
            mock_env_vars.secret_key = "prod_secret"
            app = initialize_flask_application()
            assert app.secret_key == "prod_secret"

def test_initialize_app_standard():
    app = initialize_flask_application()
    assert app is not None
    from config.configuration_variables import env_vars
    assert app.secret_key == env_vars.test_secret_key
