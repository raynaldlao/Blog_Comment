from datetime import datetime
from uuid import uuid4

from src.application.application_exceptions import FileTooLargeError, FileTypeError
from src.application.domain.file_record import FileRecord
from src.application.input_ports.file_management import FileManagementPort
from src.application.output_ports.file_storage_repository import FileStorageRepository


class FileService(FileManagementPort):
    """
    Implements the FileManagementPort input port.
    Handles file validation (extension, MIME type, size) and delegates
    persistence to a FileStorageRepository adapter.
    """

    _ALLOWED_EXTENSIONS: set[str] = {
        "jpg", "jpeg", "png", "gif", "webp", "avif", "svg", "bmp", "tiff", "tif",
    }
    _MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB

    def __init__(self, file_storage_repository: FileStorageRepository):
        self.file_storage_repository = file_storage_repository

    def _get_extension(self, filename: str) -> str:
        """Extract lowercase file extension from filename.

        Args:
            filename: Original filename including extension.

        Returns:
            Lowercase extension string, or empty string if no dot present.
        """
        if "." not in filename:
            return ""
        parts = filename.rsplit(".", 1)
        return parts[-1].lower()

    def _validate_extension(self, filename: str) -> None:
        """Check file extension against allowed set.

        Args:
            filename: Original filename with extension.

        Raises:
            FileTypeError: If extension is not in allowed list.
        """
        extension = self._get_extension(filename)
        if extension not in self._ALLOWED_EXTENSIONS:
            raise FileTypeError(
                f"Unsupported file extension '{extension}'. "
                f"Allowed: {', '.join(sorted(self._ALLOWED_EXTENSIONS))}."
            )

    def _validate_mime_type(self, mime_type: str) -> None:
        """Check MIME type starts with image/.

        Args:
            mime_type: MIME type string from upload.

        Raises:
            FileTypeError: If MIME type is not image/*.
        """
        if not mime_type.startswith("image/"):
            raise FileTypeError(
                f"Unsupported MIME type '{mime_type}'. Only image/* files are allowed."
            )

    def _validate_size(self, size: int) -> None:
        """Check file size does not exceed maximum.

        Args:
            size: File size in bytes.

        Raises:
            FileTooLargeError: If size exceeds max limit.
        """
        if size > self._MAX_FILE_SIZE:
            raise FileTooLargeError(
                f"File size {size} bytes exceeds the maximum allowed size "
                f"of {self._MAX_FILE_SIZE} bytes (5 MB)."
            )

    def upload_file(self, filename: str, data: bytes, mime_type: str) -> FileRecord:
        """Validate and persist an uploaded file.

        Args:
            filename: Original filename with extension.
            data: Raw binary content.
            mime_type: MIME type string.

        Returns:
            FileRecord with assigned UUID and timestamp.

        Raises:
            FileTypeError: If extension or MIME type is not allowed.
            FileTooLargeError: If size exceeds 5 MB limit.
        """
        self._validate_extension(filename)
        self._validate_mime_type(mime_type)
        self._validate_size(len(data))

        file_record = FileRecord(
            file_id=str(uuid4()),
            original_filename=filename,
            mime_type=mime_type,
            size=len(data),
            data=data,
            created_at=datetime.now(),
        )

        return self.file_storage_repository.save(file_record)

    def get_file(self, file_id: str) -> FileRecord | None:
        """Retrieve a file record by UUID.

        Args:
            file_id: UUID string of the file.

        Returns:
            FileRecord if found, None otherwise.
        """
        return self.file_storage_repository.get(file_id)

    def delete_file(self, file_id: str) -> None:
        """Delete a file record by UUID.

        Idempotent — does nothing if the file does not exist.

        Args:
            file_id: UUID string of the file to delete.
        """
        self.file_storage_repository.delete(file_id)
