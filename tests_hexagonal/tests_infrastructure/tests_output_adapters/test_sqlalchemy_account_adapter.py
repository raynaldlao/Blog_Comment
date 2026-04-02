from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.domain.account import Account, AccountRole
from src.infrastructure.config import infra_config
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel
from src.infrastructure.output_adapters.sqlalchemy.sqlalchemy_account_adapter import SqlAlchemyAccountAdapter


class SqlAlchemyAccountAdapterTestBase:
    """
    Base class for SqlAlchemyAccountAdapter integration tests.
    Connects to the PostgreSQL test database, creates tables before
    each test and truncates data after each test for inspection.
    """

    def setup_method(self):
        self.engine = create_engine(infra_config.test_database_url)
        SqlAlchemyModel.metadata.create_all(self.engine)

        with self.engine.connect() as connection:
            tables = SqlAlchemyModel.metadata.sorted_tables
            table_names = ", ".join(f'"{t.name}"' for t in tables)
            if table_names:
                from sqlalchemy import text
                connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))
                connection.commit()

        session_factory = sessionmaker(bind=self.engine)
        self.session = session_factory()
        self.repository = SqlAlchemyAccountAdapter(self.session)

    def teardown_method(self):
        self.session.rollback()
        self.session.close()
        self.engine.dispose()

    def _insert_account(
        self,
        username="testuser",
        password="password123",
        email="test@example.com",
        role="user",
    ) -> AccountModel:

        model = AccountModel()
        model.account_username = username
        model.account_password = password
        model.account_email = email
        model.account_role = role
        self.session.add(model)
        self.session.commit()
        return model


class TestFindByUsername(SqlAlchemyAccountAdapterTestBase):
    def test_find_by_username_returns_domain_account(self):
        self._insert_account(username="admin_user", role="admin")
        result = self.repository.find_by_username("admin_user")
        assert result is not None
        assert isinstance(result, Account)
        assert result.account_username == "admin_user"
        assert result.account_role == AccountRole.ADMIN

    def test_find_by_username_not_found_returns_none(self):
        result = self.repository.find_by_username("nonexistent")
        assert result is None

    def test_find_by_username_returns_correct_password(self):
        self._insert_account(username="login_test", password="secret123")
        result = self.repository.find_by_username("login_test")
        assert result is not None
        assert result.account_password == "secret123"


class TestFindByEmail(SqlAlchemyAccountAdapterTestBase):
    def test_find_by_email_returns_domain_account(self):
        self._insert_account(email="found@example.com", role="author")
        result = self.repository.find_by_email("found@example.com")
        assert result is not None
        assert isinstance(result, Account)
        assert result.account_email == "found@example.com"
        assert result.account_role == AccountRole.AUTHOR

    def test_find_by_email_not_found_returns_none(self):
        result = self.repository.find_by_email("ghost@nowhere.com")
        assert result is None

    def test_find_by_email_returns_correct_username(self):
        self._insert_account(username="email_owner", email="owner@blog.com")
        result = self.repository.find_by_email("owner@blog.com")
        assert result is not None
        assert result.account_username == "email_owner"


class TestGetById(SqlAlchemyAccountAdapterTestBase):
    def test_get_by_id_returns_domain_account(self):
        inserted = self._insert_account(username="id_user", role="user")
        result = self.repository.get_by_id(inserted.account_id)
        assert result is not None
        assert isinstance(result, Account)
        assert result.account_username == "id_user"
        assert result.account_role == AccountRole.USER

    def test_get_by_id_not_found_returns_none(self):
        result = self.repository.get_by_id(99999)
        assert result is None


class TestSave(SqlAlchemyAccountAdapterTestBase):
    def test_save_persists_account_to_database(self):
        account = Account(
            account_id=0,
            account_username="new_user",
            account_password="hashed_pwd",
            account_email="new@example.com",
            account_role=AccountRole.USER,
            account_created_at=None,
        )

        self.repository.save(account)
        model = self.session.query(AccountModel).filter_by(account_username="new_user").first()
        assert model is not None
        assert model.account_email == "new@example.com"
        assert model.account_role == "user"

    def test_save_account_is_retrievable_via_adapter(self):
        account = Account(
            account_id=0,
            account_username="round_trip",
            account_password="secure",
            account_email="round@trip.com",
            account_role=AccountRole.AUTHOR,
            account_created_at=None,
        )

        self.repository.save(account)
        result = self.repository.find_by_username("round_trip")
        assert result is not None
        assert result.account_email == "round@trip.com"
        assert result.account_role == AccountRole.AUTHOR

    def test_save_assigns_auto_generated_id(self):
        account = Account(
            account_id=0,
            account_username="auto_id",
            account_password="pass",
            account_email="auto@id.com",
            account_role=AccountRole.USER,
            account_created_at=None,
        )

        self.repository.save(account)
        result = self.repository.find_by_username("auto_id")
        assert result is not None
        assert result.account_id > 0
