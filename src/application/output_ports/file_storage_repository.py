from abc import ABC, abstractmethod

from src.application.domain.file_record import FileRecord


class FileStorageRepository(ABC):
    """
    Output port (interface) for file persistence operations.
    Defines how the application stores and retrieves uploaded files.
    """

    @abstractmethod
    def save(self, file_record: FileRecord) -> FileRecord:
        """
        Persists a file record to the database.

        Args:
            file_record (FileRecord): The file record to save.

        Returns:
            FileRecord: The saved file record with ID assigned.
        """
        pass

    @abstractmethod
    def get(self, file_id: str) -> FileRecord | None:
        """
        Retrieves a file record by its UUID.

        Args:
            file_id (str): The UUID of the file.

        Returns:
            FileRecord | None: The file record if found, None otherwise.
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
