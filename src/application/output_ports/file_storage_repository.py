from abc import ABC, abstractmethod

from src.application.domain.uploaded_file import UploadedFile


class FileStorageRepository(ABC):
    """
    Output port (interface) for file persistence operations.
    Defines how the application stores and retrieves uploaded files.
    """

    @abstractmethod
    def save(self, file_record: UploadedFile) -> UploadedFile:
        """
        Persists a file record to the database.

        Args:
            file_record (UploadedFile): The file record to save.

        Returns:
            UploadedFile: The saved file record with ID assigned.
        """
        pass

    @abstractmethod
    def get(self, file_id: str) -> UploadedFile | None:
        """
        Retrieves a file record by its UUID.

        Args:
            file_id (str): The UUID of the file.

        Returns:
            UploadedFile | None: The file record if found, None otherwise.
        """
        pass

    @abstractmethod
    def delete(self, file_id: str) -> None:
        """
        Deletes a file record by its UUID.

        Idempotent — does nothing if the file does not exist.

        Args:
            file_id (str): The UUID of the file to delete.
        """
        pass
