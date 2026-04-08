from src.application.domain.account import AccountRole
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter import SqlAlchemyAccountAdapter
from tests_hexagonal.test_domain_factories import create_test_account
from tests_hexagonal.tests_infrastructure.tests_output_adapters.tests_sqlalchemy.sqlalchemy_test_utils import (
    AccountDataBuilder,
    SqlAlchemyTestBase,
)


class SqlAlchemyAccountAdapterTestBase(SqlAlchemyTestBase):
    def setup_method(self):
        super().setup_method()
        self.repository = SqlAlchemyAccountAdapter(self.session)
        self.account_builder = AccountDataBuilder(self.session)


class TestAccountFindByUsername(SqlAlchemyAccountAdapterTestBase):
    def test_find_by_username_returns_domain_account(self):
        self.account_builder.create(username="admin_user", role="admin")
        result = self.repository.find_by_username("admin_user")
        assert result is not None
        from src.application.domain.account import Account
        assert isinstance(result, Account)
        assert result.account_username == "admin_user"
        assert result.account_role == AccountRole.ADMIN

    def test_find_by_username_not_found_returns_none(self):
        result = self.repository.find_by_username("nonexistent")
        assert result is None

    def test_find_by_username_returns_correct_password(self):
        self.account_builder.create(username="login_test", password="secret123")
        result = self.repository.find_by_username("login_test")
        assert result is not None
        assert result.account_password == "secret123"


class TestAccountFindByEmail(SqlAlchemyAccountAdapterTestBase):
    def test_find_by_email_returns_domain_account(self):
        self.account_builder.create(email="found@example.com", role="author")
        result = self.repository.find_by_email("found@example.com")
        assert result is not None
        from src.application.domain.account import Account
        assert isinstance(result, Account)
        assert result.account_email == "found@example.com"
        assert result.account_role == AccountRole.AUTHOR

    def test_find_by_email_not_found_returns_none(self):
        result = self.repository.find_by_email("ghost@nowhere.com")
        assert result is None

    def test_find_by_email_returns_correct_username(self):
        self.account_builder.create(username="email_owner", email="owner@blog.com")
        result = self.repository.find_by_email("owner@blog.com")
        assert result is not None
        assert result.account_username == "email_owner"


class TestAccountGetById(SqlAlchemyAccountAdapterTestBase):
    def test_get_by_id_returns_domain_account(self):
        inserted = self.account_builder.create(username="id_user", role="user")
        result = self.repository.get_by_id(inserted.account_id)
        assert result is not None
        from src.application.domain.account import Account
        assert isinstance(result, Account)
        assert result.account_username == "id_user"
        assert result.account_role == AccountRole.USER

    def test_get_by_id_not_found_returns_none(self):
        result = self.repository.get_by_id(99999)
        assert result is None


class TestAccountSave(SqlAlchemyAccountAdapterTestBase):
    def test_save_persists_account_to_database(self):
        account = create_test_account(
            account_id=0,
            account_username="new_user",
            account_password="hashed_pwd",
            account_email="new@example.com",
            account_role=AccountRole.USER,
        )

        self.repository.save(account)
        model = self.session.query(AccountModel).filter_by(account_username="new_user").first()
        assert model is not None
        assert model.account_email == "new@example.com"
        assert model.account_role == "user"

    def test_save_account_is_retrievable_via_adapter(self):
        account = create_test_account(
            account_id=0,
            account_username="round_trip",
            account_password="secure",
            account_email="round@trip.com",
            account_role=AccountRole.AUTHOR,
        )

        self.repository.save(account)
        result = self.repository.find_by_username("round_trip")
        assert result is not None
        assert result.account_email == "round@trip.com"
        assert result.account_role == AccountRole.AUTHOR

    def test_save_assigns_auto_generated_id(self):
        account = create_test_account(
            account_id=0,
            account_username="auto_id",
            account_password="pass",
            account_email="auto@id.com",
            account_role=AccountRole.USER,
        )

        self.repository.save(account)
        result = self.repository.find_by_username("auto_id")
        assert result is not None
        assert result.account_id > 0
