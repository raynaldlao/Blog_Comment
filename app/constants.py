from enum import Enum


class Role(str, Enum):
    """
    Enum representing user roles within the application.
    Inherits from str to allow direct string comparisons and easy database serialization.
    """

    ADMIN = "admin"
    USER = "user"
