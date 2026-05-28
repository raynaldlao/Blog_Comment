import secrets

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from src.application.output_ports.password_hasher_repository import PasswordHasherRepository


class Argon2PasswordHasherAdapter(PasswordHasherRepository):
    """
    Argon2-based implementation of the PasswordHasherRepository port.
    Uses argon2-cffi for secure password hashing and verification.
    """

    def __init__(self, time_cost: int, memory_cost: int, parallelism: int) -> None:
        """
        Initializes the adapter with an argon2-cffi Argon2Hasher instance.

        Args:
            time_cost (int): The number of iterations.
            memory_cost (int): The amount of memory usage in KiB.
            parallelism (int): The number of parallel threads.
        """
        self._hasher = Argon2Hasher(time_cost=time_cost, memory_cost=memory_cost, parallelism=parallelism)

    def hash(self, password: str) -> str:
        """
        Hashes a plaintext password using Argon2id.

        Args:
            password (str): The plaintext password to hash.

        Returns:
            str: The Argon2id hash string.
        """
        return self._hasher.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        """
        Verifies a plaintext password against a stored hash.

        Supports both Argon2id hashes and legacy plaintext passwords.
        Legacy passwords are detected via InvalidHashError and fall back
        to a constant-time comparison to prevent user enumeration.

        Args:
            password (str): The plaintext password to verify.
            hashed_password (str): The stored Argon2id hash or legacy plaintext.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        try:
            return self._hasher.verify(hashed_password, password)
        except VerifyMismatchError:
            return False
        except InvalidHashError:
            is_correct = secrets.compare_digest(password, hashed_password)
            self._hasher.hash("dummy_password_for_timing_consistency")
            return is_correct

    def check_needs_rehash(self, hashed_password: str) -> bool:
        """
        Checks if the Argon2 hash needs re-hashing based on current parameters.

        Args:
            hashed_password (str): The stored Argon2id hash string.

        Returns:
            bool: True if it needs re-hashing, False otherwise.
        """
        try:
            return self._hasher.check_needs_rehash(hashed_password)
        except InvalidHashError:
            return True
