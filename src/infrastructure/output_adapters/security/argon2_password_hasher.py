from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError

from src.application.output_ports.password_hasher_repository import PasswordHasherRepository


class Argon2PasswordHasher(PasswordHasherRepository):
    """
    Argon2-based implementation of the PasswordHasherRepository port.
    Uses argon2-cffi for secure password hashing and verification.
    """

    def __init__(self) -> None:
        """
        Initializes the adapter with a default argon2-cffi Argon2Hasher instance.
        """
        self._hasher = Argon2Hasher()

    def hash(self, password: str) -> str:
        """
        Hashes a plaintext password using Argon2id.

        Args:
            password (str): The plaintext password to hash.

        Returns:
            str: The Argon2id hash string.
        """
        return self._hasher.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool | str:
        """
        Verifies a plaintext password against an Argon2id hash.

        Args:
            password (str): The plaintext password to verify.
            hashed_password (str): The stored Argon2id hash.

        Returns:
            bool | str: True if the password matches, or an error message string if it fails.
        """
        try:
            return self._hasher.verify(hashed_password, password)
        except VerifyMismatchError:
            return "Invalid password"
