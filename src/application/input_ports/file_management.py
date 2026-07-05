from abc import ABC, abstractmethod

from src.application.domain.file_record import FileRecord


class FileManagementPort(ABC):
    """
    Input port (interface) defining file upload and retrieval operations.
    Serves as the API of the Core for file management.
    """

    @abstractmethod
    def upload_file(self, filename: str, data: bytes, mime_type: str) -> FileRecord:
        """
        Validates and uploads a file to persistent storage.

        Args:
            filename (str): Original filename with extension.
            data (bytes): Raw binary content of the file.
            mime_type (str): MIME type of the file.

        Returns:
            FileRecord: The saved file record with ID.

        Raises:
            FileTooLargeError: If file exceeds max size.
            FileTypeError: If file type or extension is not allowed.
        """
        pass

    @abstractmethod
    def get_file(self, file_id: str) -> FileRecord | None:
        """
        Retrieves a file record by its UUID.

        Args:
            file_id (str): The UUID of the file.

        Returns:
            FileRecord | None: The file record if found, None otherwise.
        """
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> None:
        """
        Deletes a file record by its UUID.

        Idempotent — does nothing if the file does not exist.

        Args:
            file_id (str): The UUID of the file to delete.
        """
        pass
