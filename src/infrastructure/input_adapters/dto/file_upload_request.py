from pydantic import BaseModel, Field


class FileUploadRequest(BaseModel):
    """Validates file upload data at the web boundary.

    Enforces structural constraints aligned with the DB schema:
    filename max 255 chars (VARCHAR(255)), mime_type max 127 chars
    (VARCHAR(127)). All fields require at least 1 character/byte.
    Business rule validation (extension whitelist, allowed MIME types,
    file size limit) is delegated to FileService.
    """

    filename: str = Field(min_length=1, max_length=255)
    data: bytes = Field(min_length=1)
    mime_type: str = Field(min_length=1, max_length=127)
