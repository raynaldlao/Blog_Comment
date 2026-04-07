from flask import Flask

from src.infrastructure.output_adapters.session.flask_session_adapter import FlaskSessionAdapter


class TestFlaskSessionAdapter:
    def setup_method(self):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "test_secret"
        self.adapter = FlaskSessionAdapter()

    def test_store_and_retrieve_value(self):
        with self.app.test_request_context():
            self.adapter.store_value("user_id", 42)
            assert self.adapter.retrieve_value("user_id") == 42

    def test_retrieve_missing_value_returns_none(self):
        with self.app.test_request_context():
            assert self.adapter.retrieve_value("non_existent") is None

    def test_invalidate_clears_all_data(self):
        with self.app.test_request_context():
            self.adapter.store_value("key1", "value1")
            self.adapter.store_value("key2", "value2")
            self.adapter.invalidate()
            assert self.adapter.retrieve_value("key1") is None
            assert self.adapter.retrieve_value("key2") is None

    def test_store_complex_types(self):
        with self.app.test_request_context():
            data_list = [1, 2, 3]
            data_dict = {"a": 1, "b": 2}
            self.adapter.store_value("my_list", data_list)
            self.adapter.store_value("my_dict", data_dict)
            assert self.adapter.retrieve_value("my_list") == data_list
            assert self.adapter.retrieve_value("my_dict") == data_dict
