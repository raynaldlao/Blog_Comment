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
