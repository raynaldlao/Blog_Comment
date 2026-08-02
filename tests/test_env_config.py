
import pytest

from config.env_config import EnvConfig


class TestEnvConfig:
    @pytest.fixture(autouse=True)
    def setup_method_fixture(self):
        self.config = EnvConfig()
        yield

    def test_database_url_reads_test_database_url(self):
        url = self.config.test_database_url
        assert url.startswith("postgresql://")

    def test_flask_env_defaults_to_development(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("FLASK_ENV", raising=False)
            new_config = EnvConfig()
            assert new_config.flask_env == "development"

    def test_flask_debug_defaults_to_false(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("FLASK_DEBUG", raising=False)
            new_config = EnvConfig()
            assert new_config.flask_debug is False

    def test_flask_debug_true_when_env_set(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("FLASK_DEBUG", "true")
            new_config = EnvConfig()
            assert new_config.flask_debug is True

    def test_argon2_time_cost_reads_env(self):
        value = self.config.argon2_time_cost
        assert isinstance(value, int)
        assert value > 0

    def test_argon2_memory_cost_reads_env(self):
        value = self.config.argon2_memory_cost
        assert isinstance(value, int)
        assert value > 0

    def test_argon2_parallelism_reads_env(self):
        value = self.config.argon2_parallelism
        assert isinstance(value, int)
        assert value > 0

    def test_missing_env_raises_runtime_error(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv("SECRET_KEY", raising=False)
            with pytest.raises(RuntimeError, match="Missing environment variable 'SECRET_KEY'"):
                EnvConfig().secret_key  # noqa: B018
