from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from src.application.domain.uploaded_file import UploadedFile


class UploadedFileRecord(BaseModel):
    """
    Pydantic DTO (Data Transfer Object) for uploaded_file database records.

    Provides validation when loading data from the persistence layer.
    Maps ORM column names (file_size, file_data) to domain attribute
    names (size, data) via to_domain().
    """

    model_config = ConfigDict(from_attributes=True)

    file_id: str

    @field_validator("file_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, value: object) -> str:
        if isinstance(value, UUID):
            return str(value)
        return str(value)

    original_filename: str
    original_filename: str
    mime_type: str
    file_size: int
    file_data: bytes
    created_at: datetime | None = None

    def to_domain(self) -> UploadedFile:
        """
        Converts the database record into a domain UploadedFile entity.

        Maps file_size to size and file_data to data to match the
        domain model attribute names.

        Returns:
            UploadedFile: The corresponding domain entity.
        """
        return UploadedFile(
            file_id=self.file_id,
            original_filename=self.original_filename,
            mime_type=self.mime_type,
            size=self.file_size,
            data=self.file_data,
            created_at=self.created_at,
        )
