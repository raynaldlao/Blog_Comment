class BlogCommentError(Exception):
    """Base for all application and infrastructure exceptions."""
    pass


class AccountAlreadyExistsError(BlogCommentError):
    """Raised when username or email already exists."""
    pass


class FileTooLargeError(BlogCommentError):
    """Raised when uploaded file exceeds max size."""
    pass


class FileTypeError(BlogCommentError):
    """Raised when uploaded file has unsupported type/extension."""
    pass


class ExceptionTest(Exception):
    """Used in tests to simulate error propagation."""
    pass
