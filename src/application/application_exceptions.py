class ApplicationError(Exception):
    """
    Base class for all business/application layer exceptions.
    """
    pass


class AccountAlreadyExistsError(ApplicationError):
    """
    Raised when attempting to create an account with a username or email
    that already exists in the database.

    This typically occurs during concurrent registration requests where
    a unique constraint violation is detected at the database level.
    """
    pass


class FileTooLargeError(ApplicationError):
    """
    Raised when an uploaded file exceeds the maximum allowed size.
    """
    pass


class FileTypeError(ApplicationError):
    """
    Raised when an uploaded file has an unsupported MIME type or extension.
    """
    pass
