from src.application.domain.uploaded_file import UploadedFile
from src.application.output_ports.file_storage_repository import FileStorageRepository


class InMemoryFileStorageRepository(FileStorageRepository):
    """
    In-memory implementation of the FileStorageRepository.
    Uses a dictionary keyed by file UUID to store uploaded files,
    designed for unit testing without a real database.
    """

    def __init__(self):
        """
        Initializes the repository with an empty internal dictionary.
        """
        self._files: dict[str, UploadedFile] = {}

    def save(self, file_record: UploadedFile) -> UploadedFile:
        """
        Stores an uploaded file in memory and returns it unchanged.

        Args:
            file_record: The UploadedFile domain entity to store.

        Returns:
            The same UploadedFile instance that was passed in.
        """
        self._files[file_record.file_id] = file_record
        return file_record

    def get(self, file_id: str) -> UploadedFile | None:
        """
        Retrieves an uploaded file by its UUID.

        Args:
            file_id: UUID string of the file.

        Returns:
            UploadedFile if found, None otherwise.
        """
        return self._files.get(file_id)

    def delete(self, file_id: str) -> None:
        """
        Deletes an uploaded file by its UUID.

        Idempotent — does nothing if the file does not exist.

        Args:
            file_id: UUID string of the file to delete.
        """
        self._files.pop(file_id, None)
