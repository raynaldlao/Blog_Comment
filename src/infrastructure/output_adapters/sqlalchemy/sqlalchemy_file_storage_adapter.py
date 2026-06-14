from sqlalchemy.orm import Session

from src.application.domain.file_record import FileRecord
from src.application.output_ports.file_storage_repository import FileStorageRepository
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_uploaded_file_model import UploadedFileModel


class SqlAlchemyFileStorageAdapter(FileStorageRepository):
    """SQLAlchemy-based implementation of FileStorageRepository.

    Persists uploaded files as BYTEA in the uploaded_files table.
    Maps directly between UploadedFileModel (ORM) and FileRecord (domain).
    No DTO needed — FileRecord has no enums or complex conversions.
    """

    def __init__(self, session: Session):
        """Initialize with SQLAlchemy session.

        Args:
            session: Active DB session.
        """
        self._session = session

    def save(self, file_record: FileRecord) -> FileRecord:
        """Persist a file record to the database.

        Args:
            file_record: Domain entity to persist.

        Returns:
            FileRecord with assigned ID and timestamp.
        """
        model = UploadedFileModel(
            file_id=file_record.file_id,
            original_filename=file_record.original_filename,
            mime_type=file_record.mime_type,
            file_size=file_record.size,
            file_data=file_record.data,
            created_at=file_record.created_at,
        )
        self._session.add(model)
        self._session.commit()
        return file_record

    def get(self, file_id: str) -> FileRecord | None:
        """Retrieve a file record by UUID.

        Args:
            file_id: UUID string.

        Returns:
            FileRecord if found, None otherwise.
        """
        model = self._session.get(UploadedFileModel, file_id)
        if model is None:
            return None
        return FileRecord(
            file_id=str(model.file_id),
            original_filename=model.original_filename,
            mime_type=model.mime_type,
            size=model.file_size,
            data=model.file_data,
            created_at=model.created_at,
        )
