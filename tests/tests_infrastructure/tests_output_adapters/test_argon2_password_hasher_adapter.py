from config.env_config import env_config
from src.infrastructure.output_adapters.security.argon2_password_hasher_adapter import (
    Argon2PasswordHasherAdapter,
)


class TestArgon2PasswordHasherAdapter:
    def setup_method(self):
        self.hasher = Argon2PasswordHasherAdapter(
            time_cost=env_config.test_argon2_time_cost,
            memory_cost=env_config.test_argon2_memory_cost,
            parallelism=env_config.test_argon2_parallelism,
        )

    def test_hash_returns_string_and_starts_with_argon2id(self):
        hashed = self.hasher.hash("password123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed.startswith("$argon2id$")

    def test_verify_correct_password(self):
        hashed = self.hasher.hash("password123")
        assert self.hasher.verify("password123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = self.hasher.hash("password123")
        assert self.hasher.verify("wrong_password", hashed) is False

    def test_verify_legacy_plaintext(self):
        assert self.hasher.verify("plaintext", "plaintext") is True

    def test_verify_legacy_plaintext_wrong(self):
        assert self.hasher.verify("wrong", "plaintext") is False

    def test_check_needs_rehash_on_argon2_hash(self):
        hashed = self.hasher.hash("password123")
        assert self.hasher.check_needs_rehash(hashed) is False

    def test_check_needs_rehash_on_legacy_plaintext(self):
        assert self.hasher.check_needs_rehash("plaintext") is True
