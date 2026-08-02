from datetime import datetime

from src.application.domain.uploaded_file import UploadedFile
from src.infrastructure.output_adapters.dto.uploaded_file_record import UploadedFileRecord


class MockUploadedFileModel:
    """Mock object to simulate an ORM model for uploaded files."""

    def __init__(self) -> None:
        self.file_id = "abc-123"
        self.original_filename = "photo.jpg"
        self.mime_type = "image/jpeg"
        self.file_size = 2048
        self.file_data = b"fake-binary-data"
        self.created_at = datetime(2024, 6, 15, 10, 30, 0)


class TestUploadedFileRecordCreation:
    def test_create_record_with_valid_data(self):
        record = UploadedFileRecord(
            file_id="xyz-789",
            original_filename="doc.pdf",
            mime_type="application/pdf",
            file_size=4096,
            file_data=b"pdf-content",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert record.file_id == "xyz-789"
        assert record.original_filename == "doc.pdf"

    def test_create_record_from_model_attributes(self):
        record = UploadedFileRecord.model_validate(MockUploadedFileModel())
        assert record.file_id == "abc-123"
        assert record.mime_type == "image/jpeg"


class TestUploadedFileRecordToDomain:
    def test_to_domain_returns_uploaded_file_instance(self):
        record = UploadedFileRecord(
            file_id="id-1", original_filename="a.png", mime_type="image/png",
            file_size=512, file_data=b"img", created_at=datetime(2024, 1, 1),
        )
        domain = record.to_domain()
        assert isinstance(domain, UploadedFile)

    def test_to_domain_maps_fields_correctly(self):
        dt = datetime(2024, 6, 15, 10, 30, 0)
        record = UploadedFileRecord(
            file_id="abc-123", original_filename="photo.jpg", mime_type="image/jpeg",
            file_size=2048, file_data=b"fake-binary-data", created_at=dt,
        )
        domain = record.to_domain()
        assert domain.file_id == "abc-123"
        assert domain.size == 2048
        assert domain.data == b"fake-binary-data"
        assert domain.created_at == dt
