from datetime import datetime


class FileRecord:
    """
    Represents an uploaded file stored in the database.

    Attributes:
        file_id (str): UUID of the file.
        original_filename (str): Original name of the uploaded file.
        mime_type (str): MIME type of the file (image/*).
        size (int): File size in bytes.
        data (bytes): Binary content of the file.
        created_at (datetime): Timestamp of upload.
    """

    def __init__(
        self,
        file_id: str,
        original_filename: str,
        mime_type: str,
        size: int,
        data: bytes,
        created_at: datetime | None = None,
    ):
        self.file_id = file_id
        self.original_filename = original_filename
        self.mime_type = mime_type
        self.size = size
        self.data = data
        self.created_at = created_at or datetime.now()
