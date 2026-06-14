from src.infrastructure.input_adapters.dto.file_upload_request import FileUploadRequest


class TestFileUploadRequest:
    def test_file_upload_request_valid(self):
        request = FileUploadRequest(
            filename="photo.jpg",
            data=b"fake_image_data",
            mime_type="image/jpeg",
        )
        assert request.filename == "photo.jpg"
        assert request.data == b"fake_image_data"
        assert request.mime_type == "image/jpeg"
