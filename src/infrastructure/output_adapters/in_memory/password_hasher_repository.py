from src.application.output_ports.password_hasher_repository import PasswordHasherRepository


class InMemoryPasswordHasherRepository(PasswordHasherRepository):
    """
    In-memory implementation of the PasswordHasherRepository.
    Uses a deterministic prefix-based scheme for testing purposes.
    Not cryptographically secure — never use in production.
    """

    _PREFIX = "inmem_"

    def hash(self, password: str) -> str:
        """
        Hashes a password using a deterministic prefix scheme.

        The resulting hash is ``inmem_<password>``, which is reversible
        and not cryptographically secure. Intended for unit testing only.

        Args:
            password: The plaintext password to hash.

        Returns:
            A deterministic string prefixed with ``inmem_``.
        """
        return self._PREFIX + password

    def verify(self, password: str, hashed_password: str) -> bool:
        """
        Verifies a password against a hash produced by this repository.

        Args:
            password: The plaintext password to check.
            hashed_password: The hash to verify against.

        Returns:
            True if the password matches the hash, False otherwise.
        """
        return hashed_password == self._PREFIX + password

    def check_needs_rehash(self, hashed_password: str) -> bool:
        """
        Indicates whether the hash needs re-hashing.

        Always returns False since the in-memory scheme has no
        configurable parameters that could become outdated.

        Args:
            hashed_password: The hash to inspect (unused).

        Returns:
            False always.
        """
        return False
