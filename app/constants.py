from enum import Enum


class Role(str, Enum):
    """
    Enum representing user roles within the application.
    """
    ADMIN = "admin"
    AUTHOR = "author"
    USER = "user"


class SessionKey(str, Enum):
    """
    Enum representing keys used in the Flask session.
    """
    USER_ID = "user_id"
    ROLE = "role"
    USERNAME = "username"


class PaginationConfig:
    """
    Configuration for pagination settings.
    """
    ARTICLES_PER_PAGE = 10
