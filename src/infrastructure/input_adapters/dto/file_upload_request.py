from pydantic import BaseModel


class FileUploadRequest(BaseModel):
    """Validates file upload data at the web boundary.

    Performs basic structural validation (types are correct). Business rule
    validation (extension whitelist, allowed MIME types, file size limit) is
    delegated to FileService.
    """

    filename: str
    data: bytes
    mime_type: str
