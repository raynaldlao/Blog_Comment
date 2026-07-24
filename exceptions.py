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


class AuthenticationError(BlogCommentError):
    """Raised when credentials are invalid or user is not authenticated."""
    pass


class AuthorizationError(BlogCommentError):
    """Raised when user lacks permission for the requested action."""
    pass


class InsufficientPermissionsError(AuthorizationError):
    """Raised when account role does not have the required permission level."""
    pass


class AccountNotFoundError(BlogCommentError):
    """Raised when an account is not found by id, username, or email."""
    pass


class AccountBannedError(BlogCommentError):
    """Raised when an account is banned and cannot perform actions."""
    pass


class UsernameAlreadyTakenError(BlogCommentError):
    """Raised when trying to register with an existing username."""
    pass


class EmailAlreadyTakenError(BlogCommentError):
    """Raised when trying to register or update with an existing email."""
    pass


class ArticleNotFoundError(BlogCommentError):
    """Raised when an article is not found."""
    pass


class OwnershipError(BlogCommentError):
    """Raised when a user is not the owner of the resource."""
    pass


class CommentNotFoundError(BlogCommentError):
    """Raised when a comment is not found."""
    pass


class CommentAuthorizationError(AuthorizationError):
    """Raised when a user is not authorized for a comment action."""
    pass


class CommentDeletedError(BlogCommentError):
    """Raised when attempting to modify a deleted comment."""
    pass


class CommentValidationError(BlogCommentError):
    """Raised when comment content is invalid (empty, too long, etc.)."""
    pass


class ExceptionTest(Exception):
    """Used in tests to simulate error propagation."""
    pass
