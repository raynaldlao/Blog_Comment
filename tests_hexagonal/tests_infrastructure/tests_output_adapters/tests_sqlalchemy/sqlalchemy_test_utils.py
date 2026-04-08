from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.config import infra_config
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_account_model import AccountModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_article_model import ArticleModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_comment_model import CommentModel
from src.infrastructure.output_adapters.sqlalchemy.models.sqlalchemy_registry import SqlAlchemyModel


class SqlAlchemyTestBase:
    """
    Shared Base class for SQLAlchemy integration tests.
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
                connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))
                connection.commit()

        session_factory = sessionmaker(bind=self.engine)
        self.session = session_factory()

    def teardown_method(self):
        self.session.rollback()
        self.session.close()
        self.engine.dispose()


class AccountDataBuilder:
    """Specialized builder for creating Account records in test database."""

    def __init__(self, session: Session):
        self._session = session

    def create(
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
        self._session.add(model)
        self._session.commit()
        return model


class ArticleDataBuilder:
    """Specialized builder for creating Article records in test database."""

    def __init__(self, session: Session):
        self._session = session

    def create(
        self,
        author_id: int,
        title: str = "Test Title",
        content: str = "Test Content",
        published_at=None,
    ) -> ArticleModel:
        model = ArticleModel()
        model.article_author_id = author_id
        model.article_title = title
        model.article_content = content
        if published_at:
            model.article_published_at = published_at
        self._session.add(model)
        self._session.commit()
        return model


class CommentDataBuilder:
    """Specialized builder for creating Comment records in test database."""

    def __init__(self, session: Session):
        self._session = session

    def create(
        self,
        article_id: int,
        author_id: int,
        content: str = "Test Comment",
        reply_to: int | None = None,
    ) -> CommentModel:
        model = CommentModel()
        model.comment_article_id = article_id
        model.comment_written_account_id = author_id
        model.comment_reply_to = reply_to
        model.comment_content = content
        self._session.add(model)
        self._session.commit()
        return model
