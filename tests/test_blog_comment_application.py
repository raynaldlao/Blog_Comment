from unittest.mock import MagicMock, patch

from blog_comment_application import _create_output_adapters, _shutdown_db_session


class TestCreateOutputAdapters:
    def test_production_argon2_params_when_db_session_none(self):
        repos = _create_output_adapters(None)  # type: ignore[arg-type]
        hasher = repos.password_hasher_repository
        assert hasher._hasher.time_cost == 2
        assert hasher._hasher.memory_cost == 19456
        assert hasher._hasher.parallelism == 1


class TestShutdownDbSession:
    def test_shutdown_does_nothing_when_no_session(self, app_with_db):
        app_with_db.config.pop("_DB_SESSION", None)
        with app_with_db.app_context():
            _shutdown_db_session()

    def test_shutdown_removes_session_when_present(self, app_with_db):
        mock_session = MagicMock()
        app_with_db.config["_DB_SESSION"] = mock_session
        with app_with_db.app_context():
            _shutdown_db_session()
        mock_session.remove.assert_called_once()


class TestCreateApp:
    def test_create_app_registers_teardown_when_no_session_injected(self):
        mock_db_session = MagicMock()
        mock_db_session.remove.return_value = None
        with patch("blog_comment_application.setup_database", return_value=mock_db_session):
            from blog_comment_application import create_app
            app = create_app()
        assert app.config.get("_DB_SESSION") is mock_db_session
