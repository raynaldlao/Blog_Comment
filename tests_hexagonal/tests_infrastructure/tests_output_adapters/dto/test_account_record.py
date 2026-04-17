from datetime import datetime

from src.application.domain.account import Account, AccountRole
from src.infrastructure.output_adapters.dto.account_record import AccountRecord


class MockAccountModel:
    """Mock object to simulate an ORM model for Account."""

    def __init__(self) -> None:
        self.account_id = 42
        self.account_username = "orm_user"
        self.account_password = "orm_password"
        self.account_email = "orm@example.com"
        self.account_role = "author"
        self.account_created_at = datetime(2024, 6, 15)


class TestAccountRecordCreation:
    def test_create_record_with_valid_data(self):
        record = AccountRecord(
            account_id=1,
            account_username="testuser",
            account_password="hashed_password",
            account_email="test@example.com",
            account_role="user",
            account_created_at=datetime(2024, 1, 1),
        )

        assert record.account_id == 1
        assert record.account_username == "testuser"
        assert record.account_password == "hashed_password"
        assert record.account_email == "test@example.com"
        assert record.account_role == "user"
        assert record.account_created_at == datetime(2024, 1, 1)

    def test_create_record_with_null_created_at(self):
        record = AccountRecord(
            account_id=1,
            account_username="testuser",
            account_password="hashed_password",
            account_email="test@example.com",
            account_role="admin",
            account_created_at=None,
        )

        assert record.account_created_at is None

    def test_create_record_from_object_attributes(self) -> None:
        record = AccountRecord.model_validate(MockAccountModel())
        assert record.account_id == 42
        assert record.account_username == "orm_user"
        assert record.account_role == "author"


class TestAccountRecordToDomain:
    def test_to_domain_returns_account_instance(self):
        record = AccountRecord(
            account_id=1,
            account_username="testuser",
            account_password="hashed_password",
            account_email="test@example.com",
            account_role="user",
            account_created_at=datetime(2024, 1, 1),
        )

        domain_account = record.to_domain()
        assert isinstance(domain_account, Account)

    def test_to_domain_maps_all_fields_correctly(self):
        record = AccountRecord(
            account_id=5,
            account_username="admin_user",
            account_password="secure_hash",
            account_email="admin@blog.com",
            account_role="admin",
            account_created_at=datetime(2024, 3, 15, 10, 30),
        )

        domain_account = record.to_domain()

        assert domain_account.account_id == 5
        assert domain_account.account_username == "admin_user"
        assert domain_account.account_password == "secure_hash"
        assert domain_account.account_email == "admin@blog.com"
        assert domain_account.account_created_at == datetime(2024, 3, 15, 10, 30)

    def test_to_domain_converts_role_string_to_enum(self):
        role_mappings = [
            ("admin", AccountRole.ADMIN),
            ("author", AccountRole.AUTHOR),
            ("user", AccountRole.USER),
        ]

        for role_string, expected_enum in role_mappings:
            record = AccountRecord(
                account_id=1,
                account_username="testuser",
                account_password="password",
                account_email="test@example.com",
                account_role=role_string,
                account_created_at=None,
            )

            domain_account = record.to_domain()
            assert domain_account.account_role == expected_enum

    def test_to_domain_preserves_null_created_at(self):
        record = AccountRecord(
            account_id=1,
            account_username="testuser",
            account_password="password",
            account_email="test@example.com",
            account_role="user",
            account_created_at=None,
        )

        domain_account = record.to_domain()
        assert domain_account.account_created_at is None
