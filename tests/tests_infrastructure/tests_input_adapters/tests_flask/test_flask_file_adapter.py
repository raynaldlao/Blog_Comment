from io import BytesIO
from unittest.mock import Mock

from src.application.domain.file_record import FileRecord
from src.application.input_ports.file_management import FileManagementPort
from src.infrastructure.input_adapters.flask.flask_file_adapter import FlaskFileAdapter
from tests.tests_infrastructure.tests_input_adapters.tests_flask.flask_test_utils import (
    FlaskInputAdapterTestBase,
)


class FlaskFileAdapterTest(FlaskInputAdapterTestBase):
    def setup_method(self):
        super().setup_method()
        self.mock_file_service = Mock(spec=FileManagementPort, autospec=True)
        self.adapter = FlaskFileAdapter(file_service=self.mock_file_service)

        self.app.add_url_rule(
            "/api/upload/image",
            view_func=self.adapter.upload_image,
            methods=["POST"],
            endpoint="file.upload_image",
        )

        self.app.add_url_rule(
            "/uploads/<file_id>/<filename>",
            view_func=self.adapter.serve_file,
            methods=["GET"],
            endpoint="file.serve_file",
        )


class TestFileUpload(FlaskFileAdapterTest):
    def test_upload_image_success(self):
        record = FileRecord(
            file_id="uuid-123",
            original_filename="photo.jpg",
            mime_type="image/jpeg",
            data=b"fake_image_data",
            size=len(b"fake_image_data"),
        )
        self.mock_file_service.upload_file.return_value = record

        data = {"file": (BytesIO(b"fake_image_data"), "photo.jpg")}
        response = self.client.post(
            "/api/upload/image",
            data=data,
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        assert response.json is not None
        assert response.json["url"] == "/uploads/uuid-123/photo.jpg"
        self.mock_file_service.upload_file.assert_called_once_with(
            filename="photo.jpg",
            data=b"fake_image_data",
            mime_type="image/jpeg",
        )

    def test_upload_image_no_file_provided(self):
        response = self.client.post(
            "/api/upload/image",
            data={},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        assert b"No file provided" in response.data
        self.mock_file_service.upload_file.assert_not_called()

    def test_upload_image_without_filename(self):
        data = {"file": (BytesIO(b"data"), "")}
        response = self.client.post(
            "/api/upload/image",
            data=data,
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        assert b"No file provided" in response.data
        self.mock_file_service.upload_file.assert_not_called()


class TestFileServe(FlaskFileAdapterTest):
    def test_serve_file_success(self):
        record = FileRecord(
            file_id="uuid-456",
            original_filename="photo.jpg",
            mime_type="image/jpeg",
            data=b"fake_image_data",
            size=len(b"fake_image_data"),
        )
        self.mock_file_service.get_file.return_value = record

        response = self.client.get("/uploads/uuid-456/photo.jpg")

        assert response.status_code == 200
        assert response.mimetype == "image/jpeg"
        assert response.data == b"fake_image_data"
        self.mock_file_service.get_file.assert_called_once_with("uuid-456")

    def test_serve_file_not_found(self):
        self.mock_file_service.get_file.return_value = None

        response = self.client.get("/uploads/uuid-999/missing.jpg")

        assert response.status_code == 404
        assert b"File not found" in response.data
        self.mock_file_service.get_file.assert_called_once_with("uuid-999")
