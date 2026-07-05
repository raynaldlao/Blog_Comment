from unittest.mock import MagicMock

from src.application.application_exceptions import FileTooLargeError, FileTypeError
from src.application.domain.file_record import FileRecord
from src.application.output_ports.file_storage_repository import FileStorageRepository
from src.application.services.file_service import FileService


class TestFileService:
    def setup_method(self):
        self.mock_storage = MagicMock(spec=FileStorageRepository, autospec=True)
        self.mock_storage.save.side_effect = lambda x: x
        self.service = FileService(file_storage_repository=self.mock_storage)

    def test_upload_file_valid_image(self):
        result = self.service.upload_file(
            filename="photo.jpg",
            data=b"fake_image_data",
            mime_type="image/jpeg",
        )

        self.mock_storage.save.assert_called_once()
        assert isinstance(result, FileRecord)
        assert result.original_filename == "photo.jpg"
        assert result.mime_type == "image/jpeg"
        assert result.size == len(b"fake_image_data")

    def test_upload_file_uppercase_extension(self):
        result = self.service.upload_file(
            filename="photo.JPG",
            data=b"fake",
            mime_type="image/jpeg",
        )

        self.mock_storage.save.assert_called_once()
        assert result.original_filename == "photo.JPG"

    def test_upload_file_invalid_extension(self):
        import pytest
        with pytest.raises(FileTypeError, match="txt"):
            self.service.upload_file(
                filename="notes.txt",
                data=b"some content",
                mime_type="text/plain",
            )
        self.mock_storage.save.assert_not_called()

    def test_upload_file_non_image_mime(self):
        import pytest
        with pytest.raises(FileTypeError, match="application/pdf"):
            self.service.upload_file(
                filename="image.png",
                data=b"fake",
                mime_type="application/pdf",
            )
        self.mock_storage.save.assert_not_called()

    def test_upload_file_too_large(self):
        import pytest
        large_data = b"x" * (5 * 1024 * 1024 + 1)
        with pytest.raises(FileTooLargeError, match="5242881"):
            self.service.upload_file(
                filename="huge.png",
                data=large_data,
                mime_type="image/png",
            )
        self.mock_storage.save.assert_not_called()

    def test_get_file_found(self):
        expected = FileRecord(
            file_id="uuid-789",
            original_filename="found.png",
            mime_type="image/png",
            size=256,
            data=b"found",
        )
        self.mock_storage.get.return_value = expected

        result = self.service.get_file("uuid-789")

        self.mock_storage.get.assert_called_once_with("uuid-789")
        assert result is expected

    def test_get_file_not_found(self):
        self.mock_storage.get.return_value = None

        result = self.service.get_file("uuid-missing")

        self.mock_storage.get.assert_called_once_with("uuid-missing")
        assert result is None

    def test_delete_file_delegates_to_storage(self):
        self.service.delete_file("uuid-to-delete")

        self.mock_storage.delete.assert_called_once_with("uuid-to-delete")
