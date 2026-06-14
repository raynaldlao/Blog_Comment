import pytest
from uuid import uuid4

from src.application.domain.file_record import FileRecord
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_file_storage_adapter import SqlAlchemyFileStorageAdapter
from tests.tests_infrastructure.tests_output_adapters.tests_sqlalchemy.sqlalchemy_test_utils import SqlAlchemyTestBase


class TestSqlAlchemyFileStorageAdapter(SqlAlchemyTestBase):
    @pytest.fixture(autouse=True)
    def setup_adapter(self, db_engine):
        adapter = SqlAlchemyFileStorageAdapter(self.session)
        self.repository = adapter

    def test_save_and_get(self):
        file_record = FileRecord(
            file_id=str(uuid4()),
            original_filename="test.png",
            mime_type="image/png",
            size=1024,
            data=b"fake_image_data",
        )

        saved = self.repository.save(file_record)
        assert saved.file_id == file_record.file_id
        assert saved.original_filename == "test.png"

        retrieved = self.repository.get(file_record.file_id)
        assert retrieved is not None
        assert retrieved.file_id == file_record.file_id
        assert retrieved.original_filename == "test.png"
        assert retrieved.mime_type == "image/png"
        assert retrieved.size == 1024
        assert retrieved.data == b"fake_image_data"

    def test_get_not_found_returns_none(self):
        result = self.repository.get("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_save_preserves_binary_data(self):
        binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        file_record = FileRecord(
            file_id=str(uuid4()),
            original_filename="tiny.png",
            mime_type="image/png",
            size=len(binary_data),
            data=binary_data,
        )

        self.repository.save(file_record)
        retrieved = self.repository.get(file_record.file_id)

        assert retrieved is not None
        assert retrieved.data == binary_data
        assert retrieved.size == len(binary_data)
