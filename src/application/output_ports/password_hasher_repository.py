from abc import ABC, abstractmethod


class PasswordHasherRepository(ABC):
    """
    Output port defining the contract for password hashing operations.
    Any infrastructure adapter (Argon2, bcrypt, etc.) must implement
    this interface.
    """

    @abstractmethod
    def hash(self, password: str) -> str:
        """
        Hashes a plaintext password.

        Args:
            password (str): The plaintext password to hash.

        Returns:
            str: The resulting password hash string.
        """
        pass

    @abstractmethod
    def verify(self, password: str, hashed_password: str) -> bool:
        """
        Verifies a plaintext password against a hashed password.

        Args:
            password (str): The plaintext password to verify.
            hashed_password (str): The stored hash to verify against.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        pass

    @abstractmethod
    def check_needs_rehash(self, hashed_password: str) -> bool:
        """
        Checks if the given hash needs to be re-hashed according to current
        security parameters.

        Args:
            hashed_password (str): The hash to check.

        Returns:
            bool: True if it needs re-hashing, False otherwise.
        """
        pass
